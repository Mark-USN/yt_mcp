# modules_registrar.py
"""
Dynamic discovery and registration of MCP tools, prompts, and resources.
This loader automatically scans a package for lib (.py files),
imports them safely, and registers them into an MCP server.
"""
from __future__ import annotations

import sys
import importlib
import importlib.util
import pkgutil
from types import ModuleType
from typing import Any, List, TypeVar
from pathlib import Path
import textwrap
import frontmatter  # pip/uv: python-frontmatter
from fastmcp import FastMCP
from fastmcp.resources import FileResource, TextResource, DirectoryResource
from yt_lib.utils.log_utils import get_logger # , log_tree
from yt_lib.utils.app_context import RuntimeContext


T = TypeVar("T", bound=FastMCP)

# -----------------------------
# Logging setup
# -----------------------------
logger = get_logger(__name__)

class ModuleLoaderError(Exception):
    """Custom exception for module loading errors."""
class ModuleRegistrationError(Exception):
    """Custom exception for module registration errors."""
class ModuleDiscoveryError(Exception):
    """Custom exception for module discovery errors."""
class ModuleImportError(Exception):
    """Custom exception for module import errors."""
#=================================================
#
# Base class for Registrars methods
#
#=================================================

class RegistrarBase:
    """ Base class for different types of registrars (tools, prompts, resources). """
    def __init__(self, mcp: FastMCP, app_ctx: RuntimeContext, module_dir: Path | str) -> None:
        """ Initialize the registrar with the MCP server, application context, and module directory.
            Args:
                mcp (FastMCP): The MCP server instance to register tools/prompts/resources with.
                app_ctx (RuntimeContext): The runtime context of the application.
                module_dir (Path | str): The directory containing the modules to be registered.
        """
        self.mcp_server = mcp
        self.ctx = app_ctx
        self.base_dir = app_ctx.app_dir.parents[1].resolve()
        self.module_dir = Path(module_dir).resolve()

        if not self.module_dir.is_dir():
            raise ModuleLoaderError(f"Not a directory: {self.module_dir}")

    def register(self) -> None:
        """ Abstract method to be implemented by subclasses to perform the actual registration 
            logic. 
        """
        raise NotImplementedError

#=================================================
#
# PyRegistrar methods in Python modules.
#
#=================================================

class PyRegistrar(RegistrarBase):
    """ Register .py Modules in the given directory.  Will work for Tools, Prompts, and Resource 
        py files.
    """


    def register_modules_with_server(self, module: ModuleType) -> None:
        """ Register all registered methods from a specific module.
            Args:
                module (ModuleType): The module containing a register(mcp) method.
        """
        if not hasattr(module, "register"):
            logger.warning("Module %s has no register(mcp) function", module.__name__)
            return

        module.register(self.mcp_server, self.ctx)
        logger.info("🔧 Registered methods from %s", module.__name__)

    def discover_modules(self, package: str) -> List[ModuleType]:
        """ Discover all module libs inside the given package.
            Args:
                package (str): Python package path containing the python libs.
            Returns:
                List[ModuleType]: A list of successfully imported module.
            Raises:
                ModuleDiscoveryError: If the package cannot be imported or no modules are found.
        """
        try:
            pkg = importlib.import_module(package)
        except ImportError as exc:
            logger.error("Could not import package '%s': %s", package, exc)
            return []

        modules: List[ModuleType] = []

        for _, modname, ispkg in pkgutil.iter_modules(pkg.__path__):
            if ispkg :
                continue

            full_name = f"{package}.{modname}"
            try:
                module = importlib.import_module(full_name)
                modules.append(module)
                logger.info("Loaded method lib: %s into module %s", full_name, package)
            except Exception as exc:      # pylint: disable=broad-exception-caught
                logger.exception("Error importing lib %s: %s", full_name, exc)
                continue

        return modules


    def package_name_from_module_dir(self) -> str:
        """ Derive the Python package name from the module directory path, relative to the
            base directory.
            Returns:
                str: The Python package name.
            Raises:
                ModuleLoaderError: If the module directory is not under the base directory.
        """
        root = self.base_dir.resolve()
        module_dir = self.module_dir.resolve()

        try:
            relative_dir = module_dir.relative_to(root)
        except ValueError as exc:
            raise ModuleLoaderError(
                f"module_dir must be under base_dir:\n"
                f"  module_dir: {module_dir}\n"
                f"  base_dir:   {root}"
            ) from exc

        return ".".join(relative_dir.parts)


    def load_package_from_directory(self) -> tuple[ModuleType, str]:
        """ Load the Python package from the module directory, ensuring it has an __init__.py
            file.
            Returns:
                tuple[ModuleType, str]: The imported package module and its name.
        """
        package_name = self.package_name_from_module_dir()

        init_file = self.module_dir / "__init__.py"
        if not init_file.is_file():
            raise ModuleLoaderError(f"Missing package file: {init_file}")

        base_text = str(self.base_dir)
        if base_text not in sys.path:
            sys.path.insert(0, base_text)

        package = importlib.import_module(package_name)
        return package, package_name

    def register(self) -> None:
        """ Register all discovered and qualifying .py files with the MCP server. """
        _, module_name = self.load_package_from_directory()

        modules = self.discover_modules(module_name)
        if not modules:
            logger.warning("No method lib found in package '%s'", module_name)

        for module in modules:
            self.register_modules_with_server(module)

#==========================================================
#
# PromptRegistrar Load, parse, and register markdown files
#
#==========================================================

class PromptRegistrar(RegistrarBase):
    """ Register .py Modules in the given directory.  Will work for Tools, Prompts, and Resource 
        py files.
    """

    def normalize_params(self, raw_params: Any) -> dict[str, dict[str, Any]]:
        """ Normalize the 'params' block from YAML into a dict:
            { name: {description, required, default, type} }
            Args:
                raw_params: The raw 'params' block from YAML.
            Returns:
                A dictionary of normalized parameters.
            Accepts either:
              - a mapping: params: { text: { ... }, lang: { ... } }
              - or a list of dicts: params: [ {name: text, ...}, {name: lang, ...} ]
        """
        if not raw_params:
            return {}

        params: dict[str, dict[str, Any]] = {}

        # Case 1: mapping style
        if isinstance(raw_params, dict):
            for name, cfg in raw_params.items():
                if cfg is None:
                    cfg = {}
                elif not isinstance(cfg, dict):
                    # e.g. params: {text: "some description"}
                    cfg = {"description": str(cfg)}

                name_str = str(name)
                params[name_str] = {
                    "description": cfg.get("description"),
                    "required": bool(cfg.get("required", True)),
                    "default": cfg.get("default"),
                    "type": cfg.get("type", "string"),
                }
            return params

        # Case 2: list-of-dicts style
        if isinstance(raw_params, list):
            for item in raw_params:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                if not name:
                    continue
                name_str = str(name)
                params[name_str] = {
                    "description": item.get("description"),
                    "required": bool(item.get("required", True)),
                    "default": item.get("default"),
                    "type": item.get("type", "string"),
                }
            return params

        logger.warning("Unsupported 'params' format in front matter: %r", raw_params)
        return {}

    def make_dynamic_prompt_fn(self, name: str, prompt_body: str, params: dict[str, dict]):
        """ Create a function with a real dynamic signature that FastMCP accepts.
            Args:
                name: The name of the function to create.
                prompt_body: The body of the prompt template with {placeholders}.
                params: A dict of parameter metadata, keyed by parameter name.
            Returns:
                A callable function that renders the prompt with parameters.
        """

        # Build the function signature text
        parts = []
        for p, cfg in params.items():
            if "default" in cfg:
                default = repr(cfg["default"])
                parts.append(f"{p}={default}")
            else:
                parts.append(p)
        arglist = ", ".join(parts) if parts else ""

        # Build the function body code
        code = f'''
def {name}({arglist}):
    values = locals()
    try:
        return """{prompt_body}""".format_map(values)
    except KeyError as exc:
        raise ValueError(
            f"Missing value for template placeholder: {{exc}}"
        )
'''

        # Prepare namespace
        ns = {}

        # Execute the function definition
        exec(textwrap.dedent(code), ns)     # pylint: disable=exec-used

        # Extract the function object
        return ns[name]

    def register_markdown_prompt(self, md_path: Path) -> None:
        """ Register a single markdown prompt file with the MCP server.
            Args:
                md_path: Path to the markdown file containing the prompt definition.
        """
        try:
            post = frontmatter.load(md_path)  # parses YAML front matter if present
        except Exception as exc:      # pylint: disable=broad-exception-caught
            logger.exception("Failed to parse front matter in %s: %s", md_path, exc)
            return

        body: str = str(post.content).strip()
        meta: dict[str, Any] = dict(post.metadata or {})

        # Core fields
        name: str = meta.get("name") or md_path.stem
        style: str = meta.get("style", "plain")
        description: str = meta.get("description") or f"Render '{name}' prompt ({style})."

        # Tags: allow string or list, always ensure "public"
        raw_tags = meta.get("tags") or ["public"]
        if isinstance(raw_tags, str):
            tags = {raw_tags}
        else:
            tags = {str(t).strip() for t in raw_tags if str(t).strip()}
        if "public" not in tags:
            tags.add("public")

        # Params: normalize to a stable dict format
        raw_params = meta.get("params")
        params_meta = self.normalize_params(raw_params)

        # Extra meta: everything not core
        extra_meta = {
            k: v
            for k, v in meta.items()
            if k not in {"name", "description", "tags", "style", "params"}
        }

        fn = self.make_dynamic_prompt_fn(name, body, params_meta)

        # Register the prompt with FastMCP
        self.mcp_server.prompt(
            name=name,
            description=description,
            tags=tags,
            meta={
                "style": style,
                "source_file": md_path.name,
                "params": params_meta,  # expose param metadata to clients
                **extra_meta,
            },
        )(fn)

        logger.info("Registered prompt '%s' from %s", name, md_path.name)

    def register_markdown_prompts(self) -> None:
        """ Discover and register all markdown prompt files in the module directory."""
        for md_path in self.module_dir.rglob("*.md"):
            self.register_markdown_prompt(md_path)

    def register(self) -> None:
        """ Register all discovered and qualifying .py files with the MCP server and
            parse and register markdown prompts.
        """
        PyRegistrar(self.mcp_server, self.ctx, self.module_dir).register()
        self.register_markdown_prompts()

#=================================================
#
# ResourcesRegistrar
#
#=================================================

class ResourcesRegistrar(RegistrarBase):
    """ Register designated methods in any py files in the target directory and then 
        register static resource files (e.g. .txt, .json) in the given directory as MCP resources. 
    """
    TEXT_SUFFIXES = {
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".json": "application/json",
        ".xml": "application/xml",
        ".html": "text/html",
        ".css": "text/css",
        ".js": "text/javascript",
    }


    def register_file_resource(self, path: Path, mime_type: str) -> None:
        """ Register a single file as a FileResource with the MCP server.
            Args:
                path (Path): The path to the file to be registered.
                mime_type (str): The MIME type of the file.
        """
        rel = path.relative_to(self.module_dir).as_posix()
        uri = f"file://{rel}"
        file_resource = FileResource(
                path=path,
                uri=uri,
                name=path.stem,
                description=f"Static resource from {rel}",
                mime_type=mime_type,
                tags={"public", "resource", "static"},
            )
        result = self.mcp_server.add_resource(file_resource)
        logger.info("Registered file resource '%s' at URI %s Result %s", path.name, uri, result)

    def register_text_resource(self, path: Path) -> None:
        """ Register a single text file as a TextResource with the MCP server.
            Args:
                path (Path): The path to the file to be registered.
                mime_type (str): The MIME type of the file.
        """
        rel = path.relative_to(self.module_dir).as_posix()
        uri = f"resource://{rel}"
        with path.open("r", encoding="utf-8-sig") as f:
            content = f.read()
        text_resource = TextResource(
            uri=uri,
            name=path.stem,
            text=content,
            tags={"public", "notification"}
        )
        result = self.mcp_server.add_resource(text_resource)
        logger.info("Registered text resource '%s' at URI %s Result %s", path.name, uri, result)

    def register_directory_resource(self, path: Path) -> None:
        """ Register a directory with the MCP server.
            Args:
                path (Path): The path to the directory to be registered.
        """
        # data_dir_path = path.relative_to(self.module_dir.parent).resolve()
        uri = f"resource://{path.stem}"
        if path.is_dir():
            data_listing_resource = DirectoryResource(
                uri=uri,
                path=path, # Path to the directory
                name=f"{path.stem} Directory Listing",
                description=f"Lists files available in the {path.stem} directory.",
                recursive=False # Set to True to list subdirectories
            )
            result = self.mcp_server.add_resource(data_listing_resource)
            logger.info("Registered directory resource '%s' at URI %s Result %s",
                        path.name, uri, result)

    def register(self) -> None:
        """ Register all .py files and static text resources with the MCP server. """
        PyRegistrar(
            self.mcp_server,
            self.ctx,
            self.module_dir,
        ).register()

        for suffix, mime_type in self.TEXT_SUFFIXES.items():
            for path in self.module_dir.rglob(f"*{suffix}"):
                if "text" in mime_type:
                    self.register_text_resource(path)
                else:
                    self.register_file_resource(path, mime_type)
        self.register_directory_resource(self.module_dir / "Public")
