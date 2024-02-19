import monai
import numpy as np
import torch
import lightning as L
from monai.networks.nets import UNETR
import itk
from monai.transforms import ( Compose, Resized, 
                              ToTensord, NormalizeIntensityd, EnsureChannelFirstd, Invertd)

class NetInference(L.LightningModule):
    def __init__(self, input_size, num_classes):
        super().__init__()

        self.model = UNETR(in_channels = 1, out_channels = num_classes, img_size = input_size, spatial_dims=2)

    def forward(self,x):
        x = self.model(x)
        return x
    
def run_lungair_seg_inference(itk_img: itk.image, model_checkpoint: str) -> itk.image:
    input_img = itk.array_from_image(itk_img).astype(int).squeeze()
    input_size = [512,512]
    num_classes = 2
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = NetInference.load_from_checkpoint(model_checkpoint, input_size=input_size, num_classes=num_classes, strict=False, map_location=device)
    model.eval() # Evaluation mode

    assert len(input_img.shape) == 2, f"Expected input image of dimension 2, got: {len(input_img.shape)}"

    pre_transforms = Compose([EnsureChannelFirstd(keys = ["image"], channel_dim = 'no_channel'),
                            ToTensord(keys = ["image"]),
                            Resized(keys=['image'], spatial_size = (512,512), mode=("bilinear")),
                            NormalizeIntensityd(keys=['image'])])

    input_dict = {}
    input_dict["image"] = input_img

    # Apply preprocessing
    transform_dict = pre_transforms(input_dict)

    # Run inference
    if torch.cuda.is_available():
        transform_img = transform_dict["image"][None].cuda() # Add in batch dimension
    else:
        transform_img = transform_dict["image"][None].cpu()

    pred = model(transform_img)

    # Output segmentation
    pred.softmax(dim = 1) # Convert to probability map
    pred = torch.argmax(pred, dim=1)
    transform_dict["infer"] = pred

    # Invert resize
    post_trans = Invertd(keys = "infer", transform = pre_transforms, orig_keys = "image", nearest_interp = True)
    output_dict = post_trans(transform_dict)

    # Output segmentation
    seg = output_dict["infer"].cpu().numpy()
    seg = seg.astype(np.ushort)
    PixelType = itk.ctype("unsigned short")
    Dimension = 3
    ImageType = itk.Image[PixelType, Dimension]
    result = itk.image_from_array(seg, ttype=ImageType)
    result.SetOrigin(itk_img.GetOrigin())
    result.SetSpacing(itk_img.GetSpacing())
    return result
