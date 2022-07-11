import tensorflow as tf
from functools import wraps
from timeit import default_timer as timer

def timed(func):
    """ Times function call """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = timer()
        out = func(*args, **kwargs)
        stop = timer()

        return stop - start, out

    return wrapper

def _change_image_range(tensor):
    """ Take image to [0, 1] """
    return (tensor - tf.reduce_min(tensor)) / (
        tf.reduce_max(tensor) - tf.reduce_min(tensor)
    )

def write_image_to_summary(image, writer, name, pre_process=None):
    if image.dtype == tf.bool:
        image = tf.cast(image, tf.float32)

    image = _change_image_range(image)
    if pre_process is not None:
        image = pre_process(image)

    # device is a workaround for github.com/tensorflow/tensorflow/issues/28007
    with tf.device("cpu:0"):
        with writer.as_default():
            tf.summary.image(name, image)

def write_image_to_png(image, filename, name):

    """ Write [0, 1] image to png file """
    if tf.rank(image) == 4:
        image = image[0]
    if name != "difference_image" and name != "change_map":
        image = _change_image_range(image)
    if name == "change_map":
        image = tf.cast(image, tf.int32)
    image = tf.cast(255 * image, tf.uint8)
    contents = tf.image.encode_png(image)
    tf.io.write_file(filename, contents)


def image_to_tensorboard(static_name=None, pre_process=None):
    """
        Create decorator to write function output with tf.summary.image.
        Wrapped function should return
            image - (batch_size, h, w)

        TensorBoard tag 'name' can be provided at decoration time as
        'static_name' or as a keyword-only argument 'name' at call time.
        If neither are provided, the decorator does nothing.

        Assumes tf.summary.experimental.get_step() is not None
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, name=None, **kwargs):
            name = name if name is not None else static_name
            out = tmp2 = func(self, *args, **kwargs)
            if self._save_images and name is not None:
                filename = self._img_dir + tf.constant(f"/{name}.png")
                write_image_to_png(tmp2, filename, name)
            return out
        return wrapper
    return decorator
