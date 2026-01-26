# ML-Driven Engineering Suite Implementation Guide

## 🎯 Overview

Implementasi sistem CrewAI yang telah ditingkatkan dari sistem dokumentasi sederhana menjadi **Software Engineering Suite** dengan fitur **Automated Quality Assurance** berbasis Machine Learning.

## 🛠️ Komponen yang Diimplementasikan

### 1. Dataset dan Machine Learning
- **File**: `code_metrics_data.csv`
- **Model**: Random Forest Classifier
- **Features**: complexity, loc, dependencies
- **Target**: bug (0=no, 1=yes)
- **Model File**: `tools/bug_predictor.joblib`

### 2. ML Analyzer Module
- **File**: `tools/ml_analyzer.py`
- **Class**: `CodeMLAnalyzer`
- **Capabilities**:
  - Automatic model training dari dataset CSV
  - Single dan batch risk analysis
  - Feature importance calculation
  - Comprehensive logging dan error handling

### 3. Enhanced Agent Roles

#### 🔍 Researcher Agent (ML Architecture Specialist)
- **File**: `agents/researcher.py`
- **Focus**: Analisis arsitektur ML dan pemilihan library
- **Tools**: ML library version checking, dependency analysis

#### ✍️ Writer Agent (Modular Code Developer)
- **File**: `agents/writer.py`
- **Focus**: Kode modular dan fungsional dengan ML integration
- **Tools**: ML code assessment, modular code template generation

#### ✅ Checker Agent (ML-Enhanced QA Engineer)
- **File**: `agents/checker.py`
- **Focus**: QA dengan ML-driven risk assessment
- **Tools**: `ml_enhanced_qa_check`, risk assessment automation

## 🚀 Cara Menggunakan

### 1. Inisialisasi ML Analyzer
```python
from tools.ml_analyzer import CodeMLAnalyzer

# Initialize analyzer (akan otomatis train model)
analyzer = CodeMLAnalyzer()

# Get model information
info = analyzer.get_model_info()
print(info)
```

### 2. Single Risk Analysis
```python
# Analyze risk untuk satu sample
result = analyzer.analyze_risk(
    complexity=15,  # Cyclomatic complexity
    loc=500,        # Lines of code
    dependencies=10 # Number of dependencies
)

print(f"Risk Score: {result['risk_score']}")
print(f"Recommendation: {result['recommendation']}")
```

### 3. Batch Analysis
```python
# Analyze multiple samples
samples = [
    {"complexity": 5, "loc": 120, "dependencies": 2},
    {"complexity": 20, "loc": 600, "dependencies": 12},
    {"complexity": 8, "loc": 200, "dependencies": 3}
]

results = analyzer.batch_analyze(samples)
for i, result in enumerate(results):
    print(f"Sample {i+1}: {result['recommendation']}")
```

### 4. Integration dengan Checker Agent
```python
# Checker agent akan otomatis menggunakan ML analysis
# Jika risk_score > 0.5, code akan dikembalikan ke Writer untuk improvement
```

## 📊 Risk Assessment Levels

| Risk Score | Risk Level | Recommendation | Action |
|------------|------------|----------------|---------|
| 0.0 - 0.3 | LOW | APPROVE - Low Risk | ✅ Accept code |
| 0.3 - 0.5 | MEDIUM | REVIEW - Medium Risk | 🔍 Manual review required |
| 0.5 - 0.7 | HIGH | REJECT - High Risk | ❌ Return to Writer |
| 0.7 - 1.0 | CRITICAL | REJECT - Very High Risk | ❌ Major revision needed |

## 🧪 Testing

### Run ML Analyzer Test
```bash
python3 test_ml_analyzer.py
```

Expected output:
```
🎉 All tests passed! ML Analyzer ready for production.
```

### Test Individual Agents
```bash
python3 agents/checker.py
python3 agents/researcher.py  
python3 agents/writer.py
```

## 📈 Model Performance

- **Training Data**: 30 samples
- **Features**: 3 (complexity, loc, dependencies)
- **Feature Importance**:
  - Complexity: ~36%
  - Lines of Code: ~36%
  - Dependencies: ~27%

## 🔧 Dependencies

```
scikit-learn>=1.8.0
pandas>=2.3.3
joblib>=1.5.3
numpy>=2.4.0
```

## 📁 File Structure

```
/home/aseps/MCP/crew/
├── code_metrics_data.csv          # ML training dataset
├── tools/
│   ├── ml_analyzer.py            # Core ML analyzer
│   └── bug_predictor.joblib      # Trained model
├── agents/
│   ├── checker.py               # ML-enhanced QA
│   ├── researcher.py            # ML architecture analysis
│   └── writer.py                # Modular code development
├── test_ml_analyzer.py          # Comprehensive testing
└── TASK_PROGRESS.md             # Implementation tracking
```

## 🚦 Workflow Integration

1. **Writer Agent** membuat kode modular
2. **Checker Agent** melakukan ML risk assessment
3. **Jika risk_score > 0.5**: Code dikembalikan ke Writer
4. **Jika risk_score ≤ 0.5**: Code diapprove untuk production
5. **Researcher Agent** menganalisis arsitektur ML

## ⚡ Key Features

- **Automated Quality Assurance**: ML-driven code risk assessment
- **Real-time Analysis**: Instant risk scoring dan recommendations
- **Batch Processing**: Analyze multiple code samples
- **Integration Ready**: Seamless integration dengan existing CrewAI agents
- **Comprehensive Logging**: Full audit trail untuk debugging
- **Error Handling**: Robust error management dan fallbacks

## 🔮 Future Enhancements

- [ ] Integration dengan CI/CD pipelines
- [ ] Advanced metrics (maintainability index, technical debt)
- [ ] Custom model training untuk specific domains
- [ ] Real-time code quality monitoring
- [ ] Integration dengan popular IDEs

## 🎉 Implementation Success

✅ **Mission Accomplished**: CrewAI telah ditingkatkan dari sistem dokumentasi menjadi **Software Engineering Suite** dengan ML-driven automated quality assurance!
