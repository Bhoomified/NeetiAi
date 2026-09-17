"""
Explainability for the expense categorizer.

Uses SHAP TreeExplainer on the XGBoost model, then maps the sparse feature
indices back to the actual n-grams (and the amount feature) that drove the
prediction. Falls back to global feature importance intersected with the
transaction's active tokens if SHAP is unavailable or fails.
"""
import numpy as np

from app.ml_categorizer import _model  # the loaded TextAmountXGBWrapper (or None)

_explainer = None
_feature_names = None
_shap_available = False

try:
    import importlib

    importlib.import_module("shap")
    _shap_available = True
except ImportError:
    print("⚠️  shap not installed — explanations will use fallback importance method")


def _build_feature_names():
    """Concatenates word n-grams + char n-grams + the amount feature, in the same
    order they're hstacked inside the wrapper's _transform()."""
    global _feature_names
    if _feature_names is not None:
        return _feature_names
    if _model is None:
        return None

    word_names = _model.word_vec.get_feature_names_out()
    char_names = _model.char_vec.get_feature_names_out()
    _feature_names = np.concatenate([word_names, char_names, np.array(["amount"])])
    return _feature_names


def _get_explainer():
    global _explainer
    if _explainer is not None:
        return _explainer
    if not _shap_available or _model is None:
        return None
    try:
        shap = importlib.import_module("shap")
        _explainer = shap.TreeExplainer(_model.model)
        print("✅ SHAP explainer ready for categorizer")
        return _explainer
    except Exception as e:
        print(f"⚠️  Could not build SHAP explainer: {e}")
        return None


def explain_categorization(merchant_raw: str, amount: float, top_n: int = 5) -> dict:
    """
    Returns the predicted category plus the features that pushed the model
    toward it, ranked by contribution.
    """
    if _model is None:
        return {
            "category": None,
            "confidence": None,
            "method": "unavailable",
            "contributors": [],
            "note": "No trained categorizer loaded.",
        }

    category = _model.predict([merchant_raw], [amount])[0]
    probs = _model.predict_proba([merchant_raw], [amount])
    confidence = float(probs.max())
    class_idx = int(probs.argmax())

    X = _model._transform([merchant_raw], [amount])
    feature_names = _build_feature_names()
    active_idx = X.nonzero()[1]  # only columns this transaction actually activates

    explainer = _get_explainer()

    if explainer is not None:
        try:
            X_dense = X.toarray()
            shap_out = explainer.shap_values(X_dense)

            # Multiclass SHAP returns either a list (one array per class)
            # or a 3D array (samples, features, classes) depending on version
            if isinstance(shap_out, list):
                class_shap = shap_out[class_idx][0]
            elif getattr(shap_out, "ndim", 0) == 3:
                class_shap = shap_out[0, :, class_idx]
            else:
                class_shap = shap_out[0]

            contributions = [
                {
                    "feature": str(feature_names[i]),
                    "contribution": round(float(class_shap[i]), 4),
                    "is_amount": bool(feature_names[i] == "amount"),
                }
                for i in active_idx
                if abs(float(class_shap[i])) > 1e-6
            ]
            contributions.sort(key=lambda c: abs(c["contribution"]), reverse=True)

            return {
                "category": category,
                "confidence": round(confidence, 3),
                "method": "shap",
                "contributors": contributions[:top_n],
            }
        except Exception as e:
            print(f"⚠️  SHAP explanation failed, using fallback: {e}")

    # Fallback: global feature importance restricted to this transaction's active features
    try:
        importances = _model.model.feature_importances_
        contributions = [
            {
                "feature": str(feature_names[i]),
                "contribution": round(float(importances[i]), 4),
                "is_amount": bool(feature_names[i] == "amount"),
            }
            for i in active_idx
            if importances[i] > 0
        ]
        contributions.sort(key=lambda c: c["contribution"], reverse=True)
        return {
            "category": category,
            "confidence": round(confidence, 3),
            "method": "feature_importance_fallback",
            "contributors": contributions[:top_n],
        }
    except Exception as e:
        return {
            "category": category,
            "confidence": round(confidence, 3),
            "method": "unavailable",
            "contributors": [],
            "note": f"Could not compute explanation: {e}",
        }