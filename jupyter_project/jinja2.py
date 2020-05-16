try:
    import jinja2_time
except ImportError:
    jinja2_time = None  # noqa

jinja2_extensions = list()
if jinja2_time is not None:
    jinja2_extensions.append("jinja2_time.TimeExtension")
