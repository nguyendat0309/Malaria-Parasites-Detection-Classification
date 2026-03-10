"""
Model definitions for the blood cell classifier.
Uses ConvNeXt V2 architecture with GeM pooling - matching training code exactly.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    import timm
    TIMM_AVAILABLE = True
except ImportError:
    TIMM_AVAILABLE = False
    print("Warning: timm not installed. Model loading will use mock mode.")


class GeM(nn.Module):
    """Generalized Mean Pooling."""
    def __init__(self, p=3, eps=1e-6):
        super().__init__()
        self.p = nn.Parameter(torch.ones(1) * p)
        self.eps = eps
    
    def forward(self, x):
        return F.adaptive_avg_pool2d(x.clamp(min=self.eps).pow(self.p), 1).pow(1./self.p).flatten(1)


class ConvNeXtV2Classifier(nn.Module):
    """ConvNeXt V2 classifier for blood cell classification.
    
    Architecture matches the training code exactly:
    - ConvNeXt V2 backbone (no global pooling)
    - GeM pooling
    - FC layer with BatchNorm -> ReLU
    - Final classifier
    """
    
    MODEL_NAME = "convnextv2_tiny.fcmae_ft_in22k_in1k"
    EMBEDDING_DIM = 512
    DROPOUT_RATE = 0.2
    
    def __init__(self, num_classes, model_name=None, embedding_dim=None, dropout=None):
        super().__init__()
        
        model_name = model_name or self.MODEL_NAME
        embedding_dim = embedding_dim or self.EMBEDDING_DIM
        dropout = dropout or self.DROPOUT_RATE
        
        self.num_classes = num_classes
        
        if TIMM_AVAILABLE:
            # Load backbone without classification head, no global pooling
            self.backbone = timm.create_model(
                model_name,
                pretrained=False,  # We'll load pretrained weights from checkpoint
                num_classes=0,
                global_pool=''
            )
            self.in_features = self.backbone.num_features
            
            # GeM pooling
            self.pool = GeM()
            
            # Dropout
            self.drop = nn.Dropout(dropout)
            
            # FC layer
            self.fc = nn.Linear(self.in_features, embedding_dim)
            self.bn = nn.BatchNorm1d(embedding_dim)
            
            # Classifier
            self.classifier = nn.Linear(embedding_dim, num_classes)
            self.embedding_dim = embedding_dim
        else:
            self.backbone = None
            self.embedding_dim = 512
    
    def forward(self, x, return_embeddings=False):
        if self.backbone is None:
            # Mock forward
            batch_size = x.shape[0]
            logits = torch.rand(batch_size, self.num_classes)
            if return_embeddings:
                embeddings = torch.rand(batch_size, self.embedding_dim)
                return logits, embeddings
            return logits
        
        feat = self.backbone(x)
        pooled = self.drop(self.pool(feat))
        embeddings = F.relu(self.bn(self.fc(pooled)))
        logits = self.classifier(embeddings)
        
        if return_embeddings:
            return logits, embeddings
        return logits


def load_classifier(weights_path, num_classes, device='cpu'):
    """Load a classifier model from weights file."""
    model = ConvNeXtV2Classifier(num_classes=num_classes)
    
    if TIMM_AVAILABLE and weights_path:
        try:
            print(f"Loading weights from {weights_path}...")
            checkpoint = torch.load(weights_path, map_location=device, weights_only=False)
            
            # Handle different checkpoint formats
            if isinstance(checkpoint, dict):
                if 'model' in checkpoint:
                    state_dict = checkpoint['model']
                elif 'model_state_dict' in checkpoint:
                    state_dict = checkpoint['model_state_dict']
                elif 'state_dict' in checkpoint:
                    state_dict = checkpoint['state_dict']
                else:
                    state_dict = checkpoint
            else:
                state_dict = checkpoint
            
            # Load state dict
            missing, unexpected = model.load_state_dict(state_dict, strict=False)
            
            if missing:
                print(f"  Missing keys: {len(missing)}")
            if unexpected:
                print(f"  Unexpected keys: {len(unexpected)}")
            
            print(f"  ✓ Loaded classifier weights ({num_classes} classes)")
                
        except Exception as e:
            print(f"  ✗ Could not load weights: {e}")
            import traceback
            traceback.print_exc()
    
    model.to(device)
    model.eval()
    return model
