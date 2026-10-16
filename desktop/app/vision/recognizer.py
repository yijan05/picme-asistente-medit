"""
Reconocedor facial: un One-Class SVM por usuario.

Cada usuario tiene su propio PCA + One-Class SVM. Como los modelos son
independientes, los valores crudos de `decision_function()` no son
directamente comparables entre usuarios.

Para resolverlo, cada plantilla guarda estadísticas del score producido
por su propio conjunto de entrenamiento. Durante la identificación, el
score crudo se transforma a una escala normalizada antes de compararlo
con los scores de los demás usuarios.

Las plantillas se serializan con pickle y se cifran con AES-GCM antes de
tocarse en disco (ver `security.py`).
"""
from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.decomposition import PCA
from sklearn.svm import OneClassSVM

from ..config import (
    MIN_TRAINING_SAMPLES,
    PCA_MAX_COMPONENTS,
    SVM_DECISION_MARGIN,
    SVM_GAMMA,
    SVM_NU,
)
from ..security import BiometricCipher


@dataclass
class IdentificationResult:
    user_id: Optional[int]
    score: float
    is_known: bool


class UserTemplate:
    """
    Envuelve el par (PCA, SVM) de un usuario junto con la información
    necesaria para guardarlo/cargarlo de forma cifrada.

    Además guarda estadísticas del score producido por el propio conjunto
    de entrenamiento. Estas estadísticas permiten comparar de forma más
    justa los scores de distintos One-Class SVM independientes.
    """

    def __init__(
        self,
        user_id: int,
        pca: PCA,
        svm: OneClassSVM,
        num_samples: int,
        score_center: float = 0.0,
        score_scale: float = 1.0,
    ):
        self.user_id = user_id
        self.pca = pca
        self.svm = svm
        self.num_samples = num_samples

        # Estadísticas del decision_function() sobre las muestras de
        # entrenamiento de ESTE usuario.
        self.score_center = float(score_center)
        self.score_scale = float(score_scale)

        # Nunca permitimos una escala cero o negativa.
        if not np.isfinite(self.score_center):
            self.score_center = 0.0

        if not np.isfinite(self.score_scale) or self.score_scale <= 0:
            self.score_scale = 1.0

    def decision_score(self, feature_vector: np.ndarray) -> float:
        """
        Devuelve el score crudo del One-Class SVM.

        Se mantiene este método para conservar la semántica original y
        facilitar pruebas/compatibilidad.
        """
        projected = self.pca.transform(feature_vector.reshape(1, -1))
        return float(self.svm.decision_function(projected)[0])

    def normalized_decision_score(self, feature_vector: np.ndarray) -> float:
        """
        Devuelve el score normalizado respecto a la distribución de scores
        del propio usuario durante entrenamiento.

        Un valor mayor significa que la muestra está más por encima del
        comportamiento típico aprendido por ese usuario.
        """
        raw_score = self.decision_score(feature_vector)
        return (raw_score - self.score_center) / self.score_scale

    def to_bytes(self) -> bytes:
        """
        Serializa todos los componentes necesarios para reconstruir la
        plantilla.

        Los nuevos campos de normalización se guardan junto al PCA y SVM.
        """
        return pickle.dumps(
            {
                "user_id": self.user_id,
                "pca": self.pca,
                "svm": self.svm,
                "num_samples": self.num_samples,
                "score_center": self.score_center,
                "score_scale": self.score_scale,
            }
        )

    @classmethod
    def from_bytes(cls, blob: bytes) -> "UserTemplate":
        """
        Reconstruye una plantilla serializada.

        Las plantillas antiguas pueden no tener score_center/score_scale.
        En ese caso se utiliza una normalización neutra para mantener
        compatibilidad con archivos creados antes de esta corrección.
        """
        data = pickle.loads(blob)

        return cls(
            user_id=data["user_id"],
            pca=data["pca"],
            svm=data["svm"],
            num_samples=data["num_samples"],
            score_center=data.get("score_center", 0.0),
            score_scale=data.get("score_scale", 1.0),
        )

    def save(self, path: Path, cipher: BiometricCipher) -> None:
        cipher.encrypt_file(
            self.to_bytes(),
            path,
            associated_data=str(self.user_id).encode(),
        )

    @classmethod
    def load(
        cls,
        path: Path,
        cipher: BiometricCipher,
        user_id: int,
    ) -> "UserTemplate":
        blob = cipher.decrypt_file(
            path,
            associated_data=str(user_id).encode(),
        )
        return cls.from_bytes(blob)


def _calculate_score_statistics(
    svm: OneClassSVM,
    projected_samples: np.ndarray,
) -> tuple[float, float]:
    """
    Calcula centro y escala del score del SVM sobre las muestras usadas
    para entrenarlo.

    Se utiliza desviación estándar poblacional (ddof=0), ya que estamos
    describiendo el conjunto completo de muestras de entrenamiento del
    usuario, no estimando una muestra estadística externa.

    Si todas las muestras producen exactamente el mismo score, se utiliza
    una escala mínima para evitar divisiones por cero.
    """
    training_scores = np.asarray(
        svm.decision_function(projected_samples),
        dtype=np.float64,
    ).reshape(-1)

    finite_scores = training_scores[np.isfinite(training_scores)]

    if finite_scores.size == 0:
        return 0.0, 1.0

    center = float(np.mean(finite_scores))
    scale = float(np.std(finite_scores))

    # Una distribución prácticamente constante no debe romper la
    # normalización.
    if not np.isfinite(scale) or scale < 1e-6:
        scale = 1.0

    return center, scale


def train_user_template(
    user_id: int,
    feature_vectors: np.ndarray,
) -> UserTemplate:
    """
    feature_vectors: array (N, 1404) — un vector por cada frame/ángulo
    capturado durante el registro de ESTE usuario únicamente.
    """
    if feature_vectors.ndim != 2:
        raise ValueError(
            "Se esperaba un array 2D (N muestras x dimensión del vector)"
        )

    n = feature_vectors.shape[0]

    if n < MIN_TRAINING_SAMPLES:
        raise ValueError(
            f"Se necesitan al menos {MIN_TRAINING_SAMPLES} muestras "
            f"para entrenar; se recibieron {n}"
        )

    n_components = min(PCA_MAX_COMPONENTS, n - 1)

    pca = PCA(
        n_components=n_components,
        random_state=0,
    )

    projected = pca.fit_transform(feature_vectors)

    svm = OneClassSVM(
        kernel="rbf",
        gamma=SVM_GAMMA,
        nu=SVM_NU,
    )

    svm.fit(projected)

    score_center, score_scale = _calculate_score_statistics(
        svm,
        projected,
    )

    return UserTemplate(
        user_id=user_id,
        pca=pca,
        svm=svm,
        num_samples=n,
        score_center=score_center,
        score_scale=score_scale,
    )


class Recognizer:
    """
    Carga todas las plantillas de usuario registradas y decide, para un
    vector de características nuevo, a cuál usuario pertenece o si debe
    ser considerado "Desconocido".

    Cada plantilla tiene su propio PCA + One-Class SVM. Como los scores
    crudos de modelos independientes no son directamente comparables,
    primero se normalizan usando las estadísticas aprendidas por cada
    plantilla.

    Para aceptar una identidad se deben cumplir DOS condiciones:

      1. El score crudo del One-Class SVM debe estar por encima del margen
         mínimo configurado.

      2. Entre todos los usuarios que cumplen la primera condición, se
         elige el que tenga el mayor score normalizado.

    De esta forma no se fuerza una identidad cuando ningún modelo acepta
    realmente el rostro.
    """

    def __init__(
        self,
        templates: list[UserTemplate],
        margin: float = SVM_DECISION_MARGIN,
    ):
        self._templates = templates
        self._margin = margin

    @property
    def enrolled_user_ids(self) -> list[int]:
        return [template.user_id for template in self._templates]

    def identify(
        self,
        feature_vector: np.ndarray,
    ) -> IdentificationResult:
        if not self._templates:
            return IdentificationResult(
                user_id=None,
                score=float("-inf"),
                is_known=False,
            )

        scored: list[tuple[int, float, float]] = []

        for template in self._templates:
            raw_score = template.decision_score(feature_vector)

            normalized_score = (
                raw_score - template.score_center
            ) / template.score_scale

            scored.append(
                (
                    template.user_id,
                    raw_score,
                    normalized_score,
                )
            )

        # Primero buscamos el mejor score normalizado.
        best_user_id, best_raw_score, best_normalized_score = max(
            scored,
            key=lambda item: item[2],
        )

        # La normalización sirve para COMPARAR modelos, pero no sustituye
        # al criterio original de aceptación del One-Class SVM.
        #
        # Por tanto, si el mejor modelo ni siquiera supera el margen
        # absoluto del SVM, se rechaza el rostro.
        if best_raw_score > self._margin:
            return IdentificationResult(
                user_id=best_user_id,
                score=best_normalized_score,
                is_known=True,
            )

        return IdentificationResult(
            user_id=None,
            score=best_normalized_score,
            is_known=False,
        )

    @classmethod
    def load_all(
        cls,
        template_paths: dict[int, Path],
        cipher: BiometricCipher,
    ) -> "Recognizer":
        templates = [
            UserTemplate.load(
                path,
                cipher,
                user_id,
            )
            for user_id, path in template_paths.items()
        ]

        return cls(templates)