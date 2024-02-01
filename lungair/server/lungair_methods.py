import asyncio
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor

import itk

from volview_server import (
    VolViewApi,
    get_current_client_store,
    get_current_session,
)

from volview_server.transformers import (
    convert_itk_to_vtkjs_image,
    convert_vtkjs_to_itk_image,
)

from lungair_seg_inference import run_lungair_seg_inference

## Link to app ##


volview = VolViewApi()


## median filter example ##
# copied from
# https://github.com/Kitware/VolView/blob/411e5a891bfb520647ab3f97cac6edfcca930a65/server/examples/example_api.py

process_pool = ProcessPoolExecutor(4)


@dataclass
class ClientState:
    image_id_map: dict = field(init=False, default_factory=dict)
    blurred_ids: set = field(init=False, default_factory=set)


def do_median_filter(serialized_img, radius):
    img = convert_vtkjs_to_itk_image(serialized_img)
    ImageType = type(img)

    median_filter = itk.MedianImageFilter[ImageType, ImageType].New()
    median_filter.SetInput(img)
    median_filter.SetRadius(radius)
    median_filter.Update()

    output = median_filter.GetOutput()
    return convert_itk_to_vtkjs_image(output)


async def run_median_filter_process(img, radius: int):
    serialized_img = convert_itk_to_vtkjs_image(img)
    loop = asyncio.get_event_loop()
    serialized_output = await loop.run_in_executor(
        process_pool, do_median_filter, serialized_img, radius
    )
    return convert_vtkjs_to_itk_image(serialized_output)


def associate_images(state, image_id, blurred_id):
    state.blurred_ids.add(blurred_id)
    state.image_id_map[image_id] = blurred_id
    state.image_id_map[blurred_id] = image_id


def get_base_image(state: ClientState, img_id: str) -> str:
    if img_id in state.blurred_ids:
        return state.image_id_map[img_id]
    return img_id


async def show_image(img_id: str):
    store = get_current_client_store("dataset")
    await store.setPrimarySelection({"type": "image", "dataID": img_id})


@volview.expose("medianFilter")
async def median_filter(img_id, radius):
    print(f"Started median filter on {img_id} with radius {radius}...")
    store = get_current_client_store("images")
    state = get_current_session(default_factory=ClientState)

    # Behavior: when a median filter request occurs on a
    # blurred image, we instead assume we are re-running
    # the blur operation on the original image.
    base_image_id = get_base_image(state, img_id)
    img = await store.dataIndex[base_image_id]

    # we need to run the median filter in a subprocess,
    # since itk blocks the GIL.
    output = await run_median_filter_process(img, radius)
    print(f"Completed median filter on {img_id} with radius {radius}.")

    blurred_id = state.image_id_map.get(base_image_id)
    if not blurred_id:
        blurred_id = await store.addVTKImageData("Blurred image", output)
        # Associate the blurred image ID with the base image ID.
        associate_images(state, base_image_id, blurred_id)
    else:
        await store.updateData(blurred_id, output)

    await show_image(blurred_id)

def do_lung_segmentation(serialized_img):
    itk_img = convert_vtkjs_to_itk_image(serialized_img)
    seg = run_lungair_seg_inference(itk_img, './segmentLungsModel-v1.0.ckpt')
    return convert_itk_to_vtkjs_image(seg)

async def run_lung_segmentation_process(img):
    serialized_img = convert_itk_to_vtkjs_image(img)
    loop = asyncio.get_event_loop()
    serialized_output = await loop.run_in_executor(
        process_pool, do_lung_segmentation, serialized_img
    )
    return convert_vtkjs_to_itk_image(serialized_output)

@volview.expose("segmentLungs")
async def segment_lungs(img_id):
    print(f"Started segmentLungs on {img_id} ...")
    store = get_current_client_store("images")
    state = get_current_session(default_factory=ClientState)

    # Behavior: when a filter request occurs on a
    # processed image, we instead assume we are re-running
    # the operation on the original image.
    base_image_id = get_base_image(state, img_id)
    img = await store.dataIndex[base_image_id]

    # we need to run the filter in a subprocess,
    # since itk blocks the GIL.
    segout = await run_lung_segmentation_process(img)
    print(f"Completed segmentLungs on {img_id}.")

    seg_id = state.image_id_map.get(base_image_id)
    if not seg_id:
        seg_id = await store.addVTKImageData("seg_image", segout)
        # Associate the segmented image ID with the base image ID.
        associate_images(state, base_image_id, seg_id)
    else:
        await store.updateData(seg_id, segout)

    await show_image(seg_id)
