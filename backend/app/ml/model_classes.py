"""
Shared model wrapper classes — must match EXACTLY what was defined in the
training notebook at pickle time, since joblib needs the class definition
available to reconstruct the object.
"""
import numpy as np
from scipy.sparse import hstack, csr_matrix
from sklearn.base import BaseEstimator
import re


def clean_text(text):
    text = text.lower()
    text = re.sub(r"\d{4,}", " ", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class TextAmountXGBWrapper(BaseEstimator):
    def __init__(self, word_vec, char_vec, scaler, model, label_encoder):
        self.word_vec = word_vec
        self.char_vec = char_vec
        self.scaler = scaler
        self.model = model
        self.label_encoder = label_encoder

    def _transform(self, texts, amounts):
        texts_clean = [clean_text(t) for t in texts]
        w = self.word_vec.transform(texts_clean)
        c = self.char_vec.transform(texts_clean)
        a = self.scaler.transform(np.array(amounts).reshape(-1, 1))
        return hstack([w, c, csr_matrix(a)])

    def predict(self, texts, amounts):
        preds = self.model.predict(self._transform(texts, amounts))
        return self.label_encoder.inverse_transform(preds)

    def predict_proba(self, texts, amounts):
        return self.model.predict_proba(self._transform(texts, amounts))