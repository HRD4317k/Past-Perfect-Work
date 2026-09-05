import numpy as np
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import pickle
import uvicorn

# Define FastAPI app
app = FastAPI()

# Model storage
model_pipeline = None

# Load the dataset
def load_data():
    return pd.read_csv("train.csv")  # Adjust path if needed

# Define input model for prediction and adding new data
class ProductInput(BaseModel):
    product_type: str
    original_price: float

class AddDataInput(BaseModel):
    product_type: str
    original_price: float
    depreciation: float  # Direct depreciation input

# Load the model pipeline
def load_model():
    global model_pipeline
    with open("model_pipeline.pkl", "rb") as pipeline_file:
        model_pipeline = pickle.load(pipeline_file)

@app.on_event("startup")
def startup_event():
    try:
        # Load the saved model pipeline from .pkl file
        load_model()
    except FileNotFoundError:
        raise Exception("Model pipeline file not found. Please ensure the file is available.")

# /predict endpoint to predict depreciation
@app.post("/predict")
def predict(input: ProductInput):
    if model_pipeline is None:
        return {"error": "Model not loaded yet"}

    # Prepare the input data for prediction
    product_type = input.product_type
    original_price = input.original_price

    # Prepare data as required by the model pipeline
    input_data = pd.DataFrame({
        'product_type': [product_type],
        'original_price': [original_price]
    })

    # Predict depreciation using the loaded model pipeline
    depreciation = model_pipeline.predict(input_data)
    return {"predicted_depreciation": depreciation[0]}

# /add endpoint to add new data and retrain the model
@app.post("/add")
def add_data(input: AddDataInput):
    if model_pipeline is None:
        return {"error": "Model not loaded yet"}

    # Load existing data
    df = load_data()

    # Add the new data with provided depreciation
    new_data = {
        'product_type': input.product_type,
        'original_price': input.original_price,
        'depreciation': input.depreciation
    }
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)

    # Re-train the model with the new data
    X = df[['product_type', 'original_price']]
    y = df['depreciation']

    # Update the model pipeline with the new data
    model_pipeline.fit(X, y)

    # Save the updated model pipeline
    with open("model_pipeline.pkl", "wb") as pipeline_file:
        pickle.dump(model_pipeline, pipeline_file)

    return {"message": "Data added and model retrained successfully"}
