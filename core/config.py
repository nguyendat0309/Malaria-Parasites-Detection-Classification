import os

class Config:
    MODEL_MODE_1_PHASE = "1 Phase (5-Class)"
    MODEL_MODE_2_PHASE = "2 Phase (Binary → Stages)"
    
    # Class labels - MUST match the training order exactly!
    # 1-Phase: 5-class classification
    CLASSES_5 = ["Healthy", "Ring", "Trophozoite", "Schizont", "Gametocyte"]
    
    # 2-Phase Stage 1: Binary classification
    CLASSES_BINARY = ["Healthy", "Infected"]
    
    # 2-Phase Stage 2: 4 infected stages
    CLASSES_4_STAGES = ["Ring", "Trophozoite", "Schizont", "Gametocyte"]
    
    # Dataset normalization values (from training)
    DATASET_MEAN = [0.536918, 0.504134, 0.600036]
    DATASET_STD = [0.237723, 0.259878, 0.200624]
    
    # Image size used during training
    IMG_SIZE = 256
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.selected_model_mode = self.MODEL_MODE_1_PHASE
        
        # Corrected paths
        self.yolo_weights_path = os.path.join(self.base_dir, "Weights", "Yolo", "yolo11l.pt")
        self.classifier_1phase_path = os.path.join(self.base_dir, "Weights", "ConvNext", "1Phase", "1Phase.pth")
        self.classifier_phase1_path = os.path.join(self.base_dir, "Weights", "ConvNext", "2Phase", "Phase1.pth")
        self.classifier_phase2_path = os.path.join(self.base_dir, "Weights", "ConvNext", "2Phase", "Phase2.pth")
        
        # Directories
        self.input_dir = os.path.join(self.base_dir, "Data", "Input")
        self.output_dir = os.path.join(self.base_dir, "Data", "Output")
        
    def set_model_mode(self, mode):
        self.selected_model_mode = mode
        
    def is_2_phase(self):
        return self.selected_model_mode == self.MODEL_MODE_2_PHASE

# Global instance
cfg = Config()
