import os
import PIL
import PIL.Image
import PIL.ImageChops
import numpy as np

__author__ = "Ronny Restrepo"
__copyright__ = "Copyright 2017, Ronny Restrepo"
__credits__ = ["Ronny Restrepo"]
__license__ = "Apache License"
__version__ = "2.0"


# ==============================================================================
#                                                            SHOW_TEMPLATE_IMAGE
# ==============================================================================
def show_template_image(x):
    """ Given a numpy array of 0's and 1's, representing a template/mask image
        with
            0 = background
            1 = region of interest
        it returns a PIL black and white image, with:
            white = region of interest
            black = background
    """
    PIL.Image.fromarray(x*255, mode="L").show()


# ==============================================================================
#                                                                      ARRAY2PIL
# ==============================================================================
def array2pil(x):
    """ Given a numpy array containing image information returns a PIL image.
        Automatically handles mode, and even handles greyscale images with a
        channels axis
    """
    if x.ndim == 2:
        mode = "L"
    elif x.ndim == 3 and x.shape[2] == 1:
        mode = "L"
        x = x.squeeze()
    elif x.ndim == 3:
        mode = "RGB"
    return PIL.Image.fromarray(x, mode=mode)


# ==============================================================================
#                                                                       SHOW_IMG
# ==============================================================================
def show_img(x):
    array2pil(x).show()


# ==============================================================================
#                                                        BATCH_OF_IMAGES_TO_GRID
# ==============================================================================
def batch_of_images_to_grid(imgs, rows, cols):
    """
    Given a batch of images stored as a numpy array of shape:

           [n_batch, img_height, img_width]
        or [n_batch, img_height, img_width, n_channels]

    it creates a grid of those images of shape described in `rows` and `cols`.

    Args:
        imgs: (numpy array)
            Shape should be either:
                - [n_batch, im_rows, im_cols]
                - [n_batch, im_rows, im_cols, n_channels]

        rows: (int) How many rows of images to use
        cols: (int) How many cols of images to use

    Returns: (numpy array)
        The grid of images as one large image of either shape:
            - [n_classes*im_cols, num_per_class*im_rows]
            - [n_classes*im_cols, num_per_class*im_rows, n_channels]
    """
    # TODO: have a resize option to rescale the individual sample images
    # TODO: Have a random shuffle option
    # TODO: Set the random seed if needed
    # if seed is not None:
    #     np.random.seed(seed=seed)

    # Only use the number of images needed to fill grid
    assert rows>0 and cols>0, "rows and cols must be positive integers"
    n_cells = (rows*cols)
    imgs = imgs[:n_cells]

    # Image dimensions
    n_dims = imgs.ndim
    assert n_dims==3 or n_dims==4, "Incorrect # of dimensions for input array"

    # Deal with images that have no color channel
    if n_dims == 3:
        imgs = np.expand_dims(imgs, axis=3)

    n_batch, img_height, img_width, n_channels = imgs.shape

    # Handle case where there is not enough images in batch to fill grid
    n_gap = n_cells - n_batch
    imgs = np.pad(imgs, pad_width=[(0,n_gap),(0,0), (0,0), (0,0)], mode="constant", constant_values=0)

    # Reshape into grid
    grid = imgs.reshape(rows,cols,img_height,img_width,n_channels).swapaxes(1,2)
    grid = grid.reshape(rows*img_height,cols*img_width,n_channels)

    # If input was flat images with no color channels, then flatten the output
    if n_dims == 3:
        grid = grid.squeeze(axis=2) # axis 2 because batch dim has been removed

    return grid


# ==============================================================================
#                                                         VIZ_SEGMENTATION_LABEL
# ==============================================================================
def viz_segmentation_label(label, colormap=None, saveto=None):
    """ Given a 2D numpy array representing a segmentation label, with
        the pixel value representing the class of the object, then
        it creates an RGB PIL image that color codes each label.

    Args:
        label:      (numpy array) 2D flat image where the pixel value
                    represents the class label.
        colormap:   (list of 3-tuples of ints)
                    A list where each index represents the RGB value
                    for the corresponding class id.
                    Eg: to map class_0 to black and class_1 to red:
                        [(0,0,0), (255,0,0)]
                    By default, it creates a map that supports 4 classes:

                        0. black
                        1. guava red
                        2. nice green
                        3. nice blue

        saveto:         (str or None)(default=None)(Optional)
                        File path to save the image to (as a jpg image)
    Returns:
        PIL image
    """
    # Default colormap
    if colormap is None:
        colormap = [[0,0,0], [255,79,64], [115,173,33],[48,126,199]]

    # Map each pixel label to a color
    label_viz = np.zeros((label.shape[0],label.shape[1],3), dtype=np.uint8)
    uids = np.unique(label)
    for uid in uids:
        label_viz[label==uid] = colormap[uid]

    # Convert to PIL image
    label_viz = PIL.Image.fromarray(label_viz)

    # Optionally save image
    if saveto is not None:
        # Create necessary file structure
        pardir = os.path.dirname(saveto)
        if pardir.strip() != "": # ensure pardir is not an empty string
            if not os.path.exists(pardir):
                os.makedirs(pardir)
        label_viz.save(saveto, "JPEG")

    return label_viz


# ==============================================================================
#                                               VIZ_OVERLAYED_SEGMENTATION_LABEL
# ==============================================================================
def viz_overlayed_segmentation_label(img, label, colormap=None, alpha=0.5, saveto=None):
    """ Given a base image, and the segmentation label image as numpy arrays,
        It overlays the segmentation labels on top of the base image, color
        coded for each separate class.

    Args:
        img:        (np array) numpy array containing base image (uint8 0-255)
        label:      (np array) numpy array containing segmentation labels,
                    with each pixel value representing the class label.
        colormap:   (None or list of 3-tuples) For each class label, specify
                    the RGB values to color code those pixels. Eg: red would
                    be `(255,0,0)`.
                    If `None`, then it supports up to 4 classes in a default
                    colormap:

                        0 = black
                        1 = red
                        2 = green
                        3 = blue

        alpha:      (float) Alpha value for overlayed segmentation labels
        saveto:     (None or str) Optional filepath to save this
                    visualization as a jpeg image.
    Returns:
        (PIL Image) PIL image of the visualization.
    """
    # Load the image
    img = array2pil(img)
    img = img.convert("RGB")

    # Default colormap
    if colormap is None:
        colormap = [[127,127,127],[255,0,0],[0,255,0],[0,0,255]]
    label = viz_segmentation_label(label, colormap=colormap)

    # Overlay the input image with the label
    overlay = PIL.ImageChops.blend(img, label, alpha=alpha)
    # overlay = PIL.ImageChops.add(img, label, scale=1.0)
    # overlay = PIL.ImageChops.screen(img, label)

    # Optionally save image
    if saveto is not None:
        # Create necessary file structure
        pardir = os.path.dirname(saveto)
        if pardir.strip() != "": # ensure pardir is not an empty string
            if not os.path.exists(pardir):
                os.makedirs(pardir)
        overlay.save(saveto, "JPEG")

    return overlay
