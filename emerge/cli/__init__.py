import configparser
import logging
import os
import sys

import click
from zerorpc.exceptions import RemoteError

logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s: "
    "%(levelname)s: "
    "%(funcName)s(): "
    "%(lineno)d:\t"
    "%(message)s",
)

logger = logging.getLogger(__name__)


def human_readable_size(size, decimal_places=2):
    for unit in ["B", "K", "M", "G", "T", "P"]:
        if size < 1024.0 or unit == "PiB":
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f}{unit}"


@click.group(invoke_without_command=True)
@click.option("--debug", is_flag=True, default=False, help="Debug switch")
@click.pass_context
def cli(context, debug):
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    if debug:
        logging.basicConfig(
            format="%(asctime)s : %(name)s %(levelname)s : %(message)s",
            level=logging.DEBUG,
        )
    else:
        logging.basicConfig(
            format="%(asctime)s : %(name)s %(levelname)s : %(message)s",
            level=logging.INFO,
        )

    from emerge.core.client import Client

    """ Connect to specific Node """

    context.obj = {}

    if os.path.exists("emerge.ini"):
        config = configparser.ConfigParser()
        context.obj["config"] = config.read("emerge.ini")
        client = Client(config.get("emerge", "host"), config.get("emerge", "port"))
    else:

        client = Client("0.0.0.0", "5558")

    context.obj["client"] = client
    logging.debug("Debug ON")
    if len(sys.argv) == 1:
        click.echo(context.get_help())


@cli.group()
def node():
    """Emerge node commands"""
    pass


@node.command(name="start")
@click.option("-p", "--port", default=5558, help="Listen port for server")
@click.pass_context
def start(context, port):
    """Start emerge node server"""
    from emerge.node.server import NodeServer

    node = NodeServer(port=port)
    node.setup()
    node.start()


@cli.command()
@click.argument("field", required=False, default=None)
@click.argument("query", required=False, default=None)
@click.pass_context
def search(context, field, query):
    """Search for objects"""

    client = context.obj["client"]

    if query is None:
        results = client.search(lambda o: o.path == "/inventory" and o.unit_price < 10)
    elif field is not None:
        results = client.searchtext(field, query)
    else:
        click.echo("Must provide object field")
        return

    print(results)


@cli.command()
@click.argument("query", required=False, default=None)
@click.pass_context
def hello(context, query):
    """Say hello"""
    client = context.obj["client"]

    print(client.hello(query))


@cli.command()
@click.argument("query", required=False, default=None)
@click.pass_context
def graphql(context, query):
    """graphql call"""
    client = context.obj["client"]

    print(client.graphql(query))


@cli.command()
@click.argument("path")
@click.pass_context
def rm(context, path):
    """Remove an object"""

    client = context.obj["client"]

    try:
        client.rm(path)
    except RemoteError as ex:
        print(ex.msg)


@cli.command()
@click.argument("directory")
@click.pass_context
def mkdir(context, directory):
    """Make a directory"""
    client = context.obj["client"]
    if directory[0] != "/":
        click.echo("Directory path must be absolute path e.g. /some/dir")
        return

    try:
        client.mkdir(directory)
    except RemoteError as ex:
        print(ex.msg)


@cli.command()
@click.pass_context
def cp(context):
    """Copy object command"""
    pass


@cli.command()
@click.option("-h", "--host", default="0.0.0.0", help="Hostname of server")
@click.option("-p", "--port", default="5558", help="Listen port for server")
@click.pass_context
def init(context, host, port):
    """Initialize or update the emerge.ini file"""
    config = configparser.ConfigParser()

    with open("emerge.ini", "w") as fp:
        config.add_section("emerge")
        config.set("emerge", "host", host)
        config.set("emerge", "port", port)
        config.write(fp)

    click.echo("emerge.ini updated.")


@cli.command()
@click.option("-l", "--long", is_flag=True)
@click.argument("directory", default="/")
@click.pass_context
def ls(context, long, directory):
    """List files in a directory"""

    client = context.obj["client"]

    class bcolors:
        HEADER = "\033[95m"
        OKBLUE = "\033[94m"
        OKCYAN = "\033[96m"
        OKGREEN = "\033[92m"
        WARNING = "\033[93m"
        FAIL = "\033[91m"
        ENDC = "\033[0m"
        BOLD = "\033[1m"
        UNDERLINE = "\033[4m"

    try:
        files = client.list(directory, offset=0, size=0)
    except RemoteError as ex:
        click.echo(ex.msg)
        return

    logging.debug("FILES:%s", files)
    files = reversed(sorted(files))

    for fname in files:
        if fname.find("dir") == 0:
            if fname == "dir:/" or fname == "dir:/registry":
                continue

            fname = fname.replace("dir:", "")
            logging.debug("Getting fname {}".format(fname))

            file = client.get(fname)
            if "error" in file:
                click.echo(file["message"])
                return

            logging.debug("client.get({}) = {}".format(fname, file))
            row = "{} {: <8} {: >10} {} {} {}".format(
                file["perms"],
                human_readable_size(file["size"], 1)
                if file["type"] == "file"
                else file["size"],
                file["date"],
                bcolors.OKBLUE,
                fname.replace(directory, ""),
                bcolors.ENDC,
            )

            if long:
                print(row)
            else:
                print(fname.replace(directory, ""))
        else:
            file = client.get(fname)
            if type(file) is list:
                pass
            else:
                row = "{} {: <8} {: >10} {} {: <10}".format(
                    file["perms"],
                    human_readable_size(file["size"], 1)
                    if file["type"] == "file"
                    else file["size"],
                    file["date"],
                    bcolors.ENDC,
                    file["name"],
                )

                if long:
                    print(row)
                else:
                    print(file["name"].replace(directory, ""))


@cli.command(name="query")
@click.argument("path")
@click.pass_context
def cmd_query(context, path):
    """Execute query method of an object"""
    client = context.obj["client"]

    results = client.query(path)
    print(results)


@cli.command(name="help")
@click.argument("path")
@click.pass_context
def cmd_help(context, path):
    """Display details of an objects class"""
    client = context.obj["client"]

    file = client.getobject(path, False)
    help(file)


@cli.command()
@click.argument("path")
@click.pass_context
def methods(context, path):
    """Display available methods for an object"""
    from inspect import signature

    client = context.obj["client"]

    file = client.getobject(path, False)
    method_list = [
        attribute
        for attribute in dir(type(file))
        if callable(getattr(type(file), attribute))
        and attribute.startswith("_") is False
    ]

    for method in method_list:
        print(method, signature(getattr(file, method)))


@cli.command()
@click.argument("path")
@click.pass_context
def cat(context, path):
    """Display contents of an object"""

    client = context.obj["client"]

    file = client.getobject(path, False)
    print(file)


@cli.command()
@click.argument("path")
@click.pass_context
def code(context, path):
    """List source code of an object"""

    client = context.obj["client"]

    file = client.get(path)
    print(file["source"])


@cli.command()
@click.argument("path")
@click.argument("function")
@click.option("-l", "--local", is_flag=True)
@click.pass_context
def call(context, path, function, local):
    """Call an object method"""
    client = context.obj["client"]

    if local:
        obj = client.getobject(path, False)
        method = getattr(obj, function)
        print(method())
    else:
        result = client.run(path, function)
        print(result)
