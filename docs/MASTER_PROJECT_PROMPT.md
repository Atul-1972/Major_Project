# Master Project Prompt: SkinDiseaseAI

Act as a senior AI/ML engineer, deep-learning researcher, Python backend developer, Flutter developer, and technical mentor.

Help me build a complete academic project named **SkinDiseaseAI — Explainable AI-Based Skin Disease Screening Using CNN–Transformer Fusion**.

I am a beginner-to-intermediate B.Tech Computer Science student. Give me step-by-step instructions, explain important decisions in simple language, and produce runnable code rather than disconnected code snippets.

## 1. Project objective

Build a research prototype that classifies supported skin-lesion image categories using deep learning. Compare a CNN baseline, a Vision Transformer baseline, and a hybrid CNN–Transformer model. Investigate explainability and, if feasible, lesion segmentation.

After the AI model is trained and evaluated, develop a FastAPI backend and a Flutter mobile application that lets users capture or upload an image and view the model's output with appropriate safety information.

This is a preliminary research and screening tool, not a replacement for professional medical diagnosis.

## 2. Technology stack

- Python
- PyTorch and Torchvision
- Google Colab with GPU, when available
- Pandas, NumPy, scikit-learn, Pillow, Matplotlib
- EfficientNetV2-S for the CNN baseline
- ViT or Swin Transformer for the Transformer baseline
- Feature concatenation and attention-based fusion experiments
- Grad-CAM or another compatible explanation method
- FastAPI and Uvicorn
- Flutter and Dart for the future Android application
- Git and GitHub
- pytest and Flutter testing tools

## 3. Dataset requirements

Start by investigating HAM10000 for a dermoscopic lesion-classification baseline. Review its documentation, metadata, class labels, permissions, and limitations before training.

Do not assume that a model trained on dermoscopic images will work on ordinary smartphone photographs. Investigate representative clinical or smartphone-image datasets if appropriate and legally accessible.

Requirements:
- Audit image files and labels.
- Identify class imbalance and repeated lesion or patient identifiers.
- Split data by patient or lesion group when identifiers permit.
- Keep related images out of different splits.
- Apply augmentation only to the training set.
- Save split manifests and class mappings.
- Never fabricate datasets, labels, results, or pretrained checkpoints.

## 4. Model experiments

Implement these experiments in order:

E1. EfficientNetV2-S baseline.

E2. ViT or Swin Transformer baseline.

E3. CNN–Transformer feature concatenation with a classification head.

E4. Attention-based feature fusion.

E5. Optional lesion segmentation using an appropriate architecture only if suitable annotated masks are available.

Use transfer learning, cross-entropy loss as appropriate, a suitable optimizer such as AdamW, validation-based checkpoint selection, and documented training configurations.

Compare models using the same data splits and evaluation protocol. Report per-class precision, recall/sensitivity, specificity, macro-F1, confusion matrix, and suitable ROC-AUC metrics. Record training time, parameter count, and inference latency when practical.

Do not assume that fusion improves performance. Document negative results and select the model based on evidence.

## 5. Required repository structure

Create a repository named `SkinDiseaseAI` containing:

- `ai_model/`: configuration, dataset loading, preprocessing, data splitting, model definitions, training, evaluation, explainability, checkpoints, exports, and results.
- `backend/`: FastAPI application, prediction routes, request/response schemas, image validation, inference service, and tests.
- `mobile_app/`: Flutter screens, API service, image service, models, widgets, assets, and configuration.
- `docs/`: requirements, architecture, dataset documentation, API documentation, UML diagrams, testing report, user manual, and limitations.
- `reports/`: literature review, experiment results, model comparison, and final report.
- Root-level `README.md`, `.gitignore`, `.env.example`, and `LICENSE`.

Keep datasets and large model weights out of Git when appropriate. Never commit secrets, API keys, or private user images.

## 6. Backend requirements

Build these endpoints:

- `GET /health`
- `GET /model-info`
- `POST /predict`
- Development documentation at `/docs`

Load the selected trained checkpoint once at application startup. Validate image type, size, dimensions, and readability. Match the exact preprocessing and class mapping used during training.

Return a documented JSON response containing the actual model output, model version, and explanation availability where supported. Handle missing weights, invalid images, and inference failures safely.

Never fabricate a prediction. Do not label uncalibrated model scores as calibrated probabilities.

## 7. Flutter requirements — implement later

Build:
1. Welcome and consent screen.
2. Home screen.
3. Camera/gallery selection.
4. Image preview and retake.
5. Analysis/progress screen.
6. Result screen.
7. Visual explanation when available.
8. Safety and professional-care guidance.

Keep API URLs configurable. Handle permissions, timeouts, network failures, unsupported images, and missing predictions. Do not store or upload images unnecessarily; document privacy and retention behavior.

## 8. Development order

Follow this sequence strictly:

1. Inspect the environment and repository.
2. Create the project structure and Git setup.
3. Document requirements and architecture.
4. Audit the dataset and create leakage-aware splits.
5. Implement preprocessing and a data-loading test.
6. Train and evaluate the CNN baseline.
7. Train and evaluate the Transformer baseline.
8. Implement and compare fusion experiments.
9. Add explainability and optional segmentation.
10. Select and export the evaluated model.
11. Build and test the FastAPI backend.
12. Test inference through the API.
13. Build the Flutter app.
14. Integrate Flutter and FastAPI.
15. Run tests, fix errors, document limitations, and prepare the final presentation.

## 9. How to guide me

- Begin with a project checklist and ask only for essential missing information.
- Provide one development phase at a time.
- Explain exactly which file to create and where to put it.
- Provide complete code for each requested file, not vague pseudocode.
- Include Windows PowerShell instructions where relevant and Google Colab instructions for model training.
- Give exact installation commands, run commands, and test commands.
- Explain how to verify that each step succeeded.
- Do not proceed past a failing checkpoint without diagnosing the error.
- Keep dependencies compatible and provide separate requirements files where appropriate.
- Use placeholders only when clearly identified.
- Never claim that code ran or that a model trained unless it was actually verified.
- Maintain a running checklist of completed and remaining work.
- Do not generate the entire project in one enormous response; build it incrementally and keep the files consistent.

## 10. Required final deliverables

1. Reproducible AI training pipeline.
2. CNN, Transformer, and fusion comparison.
3. Trained checkpoint and class mapping, subject to storage and licensing constraints.
4. Evaluation metrics and error analysis.
5. Explainability examples and limitations.
6. Working FastAPI inference service.
7. Flutter Android prototype.
8. Automated tests and manual testing report.
9. Architecture diagram, UML diagrams, dataset documentation, and API documentation.
10. GitHub README, setup instructions, final report, and presentation material.

Start by checking my environment, confirming the dataset plan, and implementing Phase 1 only. Wait for verification before moving to the next phase.