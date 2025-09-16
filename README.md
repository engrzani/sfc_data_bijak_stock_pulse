# SFC Data Bijak Stock Pulse

## Problem Definition

This project addresses the challenge of efficiently collecting, processing, analyzing, and modeling stock pulse data using the Data Bijak methodology. Its purpose is to automate and streamline the flow of stock market information, enabling actionable insights for traders, analysts, and stakeholders. The system manages data ingestion, transformation, training, and visualization, making complex stock data accessible and reproducible.

## Design Specification

- **Modular Data Processing:** The project is organized into clear modules for data ingestion, transformation, analysis, training, and visualization, primarily using Jupyter notebooks and Python scripts.
- **Database Integration:** Supports both MongoDB and SQLite for storing raw and processed stock data, ensuring flexibility and scalability.
- **Interactive Analysis:** Utilizes Jupyter Notebooks for step-by-step, interactive data analysis and model training.
- **Extensibility:** Designed for easy addition of new data sources, analytical methods, and visualizations.
- **Configuration Management:** Centralized configuration (`config.py`) manages database connections, data paths, and app secrets.
- **Training Phase:** Includes scripts/notebooks for training predictive models on stock data, allowing users to build, test, and validate machine learning models.

## Data Flow Diagrams

Below is a conceptual data flow for the project. For detailed, editable diagrams, users are encouraged to generate visuals based on these steps using tools like draw.io, Lucidchart, or Python visualization libraries.

### 1. Data Collection and Ingestion
```
[External Stock Data Sources]
           |
           v
[Data Ingestion Module]
           |
           v
[MongoDB / SQLite]
```

### 2. Data Transformation & Cleaning
```
[Raw Data (Database)]
           |
           v
[Transformation Scripts / Notebooks]
           |
           v
[Processed Data]
```

### 3. Training Phase
```
[Processed Data]
           |
           v
[Training Scripts / Notebooks]
           |
           v
[Trained Models]
```

### 4. Analysis & Visualization
```
[Trained Models]       [Processed Data]
         |                  |
         v                  v
   [Prediction]     [Analysis Notebooks]
         |                  |
         v                  v
[Visualizations / Reports]
```

### 5. User Interaction
```
[User]
   |
   v
[Jupyter Notebooks / Web App]
```

## Project Detailed Installation Steps

### Prerequisites

- Python 3.8 or above
- Jupyter Notebook or JupyterLab
- Git
- (Recommended) Virtual environment manager: `venv` or `conda`

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/engrzani/sfc_data_bijak_stock_pulse.git
   cd sfc_data_bijak_stock_pulse
   ```

2. **Create and Activate Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   If a `requirements.txt` file is provided, run:
   ```bash
   pip install -r requirements.txt
   ```
   Otherwise, manually install main packages:
   ```bash
   pip install numpy pandas matplotlib jupyter pymongo flask sqlalchemy scikit-learn
   ```

4. **Configure the Application**
   - Edit `SFC-DataBijak1/config.py` to update database URIs and application secrets as needed.

5. **Start Jupyter Notebook**
   ```bash
   jupyter notebook
   ```
   - Open notebooks in `SFC-DataBijak1` and follow cell instructions.

6. **Run the Analysis and Training Phase**
   - Execute notebook cells step-by-step for data ingestion, transformation, training, and visualization.
   - Training notebooks will guide you through data splits, model selection, training, and evaluation.
   - Modify parameters or add new models as needed.

### Notes

- Ensure MongoDB and/or SQLite are accessible if required by your analysis.
- For web app functionality, ensure Flask and SQLAlchemy are installed.
- For training phase, ensure machine learning libraries (e.g., scikit-learn) are installed.
- For advanced diagramming, use additional Python packages such as `matplotlib`, `plotly`, or external tools.

## References

- [Project Repository](https://github.com/engrzani/sfc_data_bijak_stock_pulse)
- [Explore SFC-DataBijak1 Folder](https://github.com/engrzani/sfc_data_bijak_stock_pulse/tree/main/SFC-DataBijak1)

---

*For more context, see code and configuration in the [`SFC-DataBijak1/config.py`](https://github.com/engrzani/sfc_data_bijak_stock_pulse/blob/main/SFC-DataBijak1/config.py).*
