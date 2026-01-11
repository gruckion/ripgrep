"""
Ripgrep client implementations.

This module provides both synchronous and asynchronous clients for ripgrep,
implementing Tier A (subprocess) integration with streaming support.
"""

import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from typing import (
    AsyncIterator,
    Iterator,
    List,
    Optional,
    Union,
    overload,
    Literal,
)

from .types import (
    Match,
    SearchStats,
    FileMatch,
    CountMatch,
    FileType,
    OutputMode,
    PathLike,
)
from .errors import (
    RipgrepError,
    PatternError,
    PathError,
    BinaryNotFoundError,
)


class Ripgrep:
    """Synchronous ripgrep client.

    This client uses subprocess to invoke ripgrep with JSON output,
    streaming results as they become available.

    Example:
        >>> rg = Ripgrep()
        >>> for match in rg.search("TODO", "src/"):
        ...     print(f"{match.path}:{match.line_number}")

        >>> # With options
        >>> for match in rg.search("pattern", ignore_case=True, context=2):
        ...     print(match.line_content)

        >>> # Files only
        >>> for path in rg.search_files("TODO", "src/"):
        ...     print(path)
    """

    def __init__(self, binary: str = "rg"):
        """Initialize ripgrep client.

        Args:
            binary: Path to ripgrep binary, or just "rg" to find in PATH.

        Raises:
            BinaryNotFoundError: If ripgrep binary is not found.
        """
        self.binary = binary
        self._binary_path = shutil.which(binary)
        if self._binary_path is None:
            raise BinaryNotFoundError(binary)

    def search(
        self,
        pattern: str,
        path: Union[PathLike, List[PathLike]] = ".",
        *,
        # Pattern options
        ignore_case: bool = False,
        smart_case: bool = False,
        word_regexp: bool = False,
        fixed_strings: bool = False,
        multiline: bool = False,
        # Context options
        context: int = 0,
        before_context: int = 0,
        after_context: int = 0,
        # File filtering
        file_type: Optional[Union[FileType, List[FileType]]] = None,
        type_not: Optional[Union[FileType, List[FileType]]] = None,
        glob: Optional[Union[str, List[str]]] = None,
        hidden: bool = False,
        no_ignore: bool = False,
        max_depth: Optional[int] = None,
        max_filesize: Optional[str] = None,
        # Output control
        max_count: Optional[int] = None,
        # Performance
        threads: Optional[int] = None,
    ) -> Iterator[Match]:
        """Search for pattern in files.

        Args:
            pattern: Regular expression pattern to search for.
            path: File or directory to search (or list of paths).
            ignore_case: Case insensitive search.
            smart_case: Smart case (insensitive unless uppercase present).
            word_regexp: Match whole words only.
            fixed_strings: Treat pattern as literal string.
            multiline: Enable multiline matching.
            context: Lines of context before and after match.
            before_context: Lines of context before match.
            after_context: Lines of context after match.
            file_type: Only search files of this type.
            type_not: Exclude files of this type.
            glob: Include/exclude files matching glob pattern.
            hidden: Search hidden files and directories.
            no_ignore: Don't respect ignore files.
            max_depth: Maximum directory depth to search.
            max_filesize: Maximum file size (e.g., "1M").
            max_count: Maximum matches per file.
            threads: Number of threads to use.

        Yields:
            Match objects for each match found.

        Raises:
            RipgrepError: If an error occurs during search.
            PatternError: If the pattern is invalid.
        """
        args = self._build_args(
            pattern=pattern,
            path=path,
            ignore_case=ignore_case,
            smart_case=smart_case,
            word_regexp=word_regexp,
            fixed_strings=fixed_strings,
            multiline=multiline,
            context=context,
            before_context=before_context,
            after_context=after_context,
            file_type=file_type,
            type_not=type_not,
            glob=glob,
            hidden=hidden,
            no_ignore=no_ignore,
            max_depth=max_depth,
            max_filesize=max_filesize,
            max_count=max_count,
            threads=threads,
            json_output=True,
        )

        yield from self._execute_streaming(args, Match.from_json)

    def search_files(
        self,
        pattern: str,
        path: Union[PathLike, List[PathLike]] = ".",
        **kwargs,
    ) -> Iterator[Path]:
        """Search and return only matching file paths.

        Same arguments as search(), but yields Path objects instead of Match.
        """
        args = self._build_args(
            pattern=pattern,
            path=path,
            files_with_matches=True,
            json_output=True,
            **kwargs,
        )

        for result in self._execute_streaming(args, FileMatch.from_json):
            yield result.path

    def search_count(
        self,
        pattern: str,
        path: Union[PathLike, List[PathLike]] = ".",
        **kwargs,
    ) -> Iterator[CountMatch]:
        """Search and return match counts per file.

        Same arguments as search(), but yields CountMatch objects.
        """
        # Count mode doesn't work well with --json, use text parsing
        args = self._build_args(
            pattern=pattern,
            path=path,
            count=True,
            json_output=False,
            **kwargs,
        )

        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            for line in proc.stdout:
                line = line.rstrip("\n")
                if line:
                    yield CountMatch.from_line(line)

            proc.wait()
            self._check_return_code(proc)
        except:
            proc.kill()
            raise

    def list_files(
        self,
        path: Union[PathLike, List[PathLike]] = ".",
        *,
        file_type: Optional[Union[FileType, List[FileType]]] = None,
        glob: Optional[Union[str, List[str]]] = None,
        hidden: bool = False,
        no_ignore: bool = False,
    ) -> Iterator[Path]:
        """List files that would be searched.

        Args:
            path: Directory to list.
            file_type: Only list files of this type.
            glob: Include/exclude files matching glob pattern.
            hidden: Include hidden files.
            no_ignore: Don't respect ignore files.

        Yields:
            Path objects for each file.
        """
        args = [self._binary_path, "--files"]

        if file_type:
            for ft in self._ensure_list(file_type):
                args.extend(["-t", ft.value])

        if glob:
            for g in self._ensure_list(glob):
                args.extend(["-g", g])

        if hidden:
            args.append("--hidden")

        if no_ignore:
            args.append("--no-ignore")

        args.extend(str(p) for p in self._ensure_list(path))

        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            for line in proc.stdout:
                yield Path(line.rstrip("\n"))

            proc.wait()
            if proc.returncode != 0:
                stderr = proc.stderr.read()
                raise RipgrepError(stderr, proc.returncode)
        except:
            proc.kill()
            raise

    def _build_args(
        self,
        pattern: str,
        path: Union[PathLike, List[PathLike]],
        *,
        json_output: bool = True,
        files_with_matches: bool = False,
        count: bool = False,
        ignore_case: bool = False,
        smart_case: bool = False,
        word_regexp: bool = False,
        fixed_strings: bool = False,
        multiline: bool = False,
        context: int = 0,
        before_context: int = 0,
        after_context: int = 0,
        file_type: Optional[Union[FileType, List[FileType]]] = None,
        type_not: Optional[Union[FileType, List[FileType]]] = None,
        glob: Optional[Union[str, List[str]]] = None,
        hidden: bool = False,
        no_ignore: bool = False,
        max_depth: Optional[int] = None,
        max_filesize: Optional[str] = None,
        max_count: Optional[int] = None,
        threads: Optional[int] = None,
    ) -> List[str]:
        """Build command-line arguments."""
        args = [self._binary_path]

        # Output format
        if json_output:
            args.append("--json")
        if files_with_matches:
            args.append("-l")
        if count:
            args.append("-c")

        # Pattern options
        if ignore_case:
            args.append("-i")
        if smart_case:
            args.append("-S")
        if word_regexp:
            args.append("-w")
        if fixed_strings:
            args.append("-F")
        if multiline:
            args.append("-U")

        # Context
        if context > 0:
            args.extend(["-C", str(context)])
        if before_context > 0:
            args.extend(["-B", str(before_context)])
        if after_context > 0:
            args.extend(["-A", str(after_context)])

        # File filtering
        if file_type:
            for ft in self._ensure_list(file_type):
                ft_val = ft.value if isinstance(ft, FileType) else str(ft)
                args.extend(["-t", ft_val])
        if type_not:
            for ft in self._ensure_list(type_not):
                ft_val = ft.value if isinstance(ft, FileType) else str(ft)
                args.extend(["-T", ft_val])
        if glob:
            for g in self._ensure_list(glob):
                args.extend(["-g", g])
        if hidden:
            args.append("--hidden")
        if no_ignore:
            args.append("--no-ignore")
        if max_depth is not None:
            args.extend(["--max-depth", str(max_depth)])
        if max_filesize is not None:
            args.extend(["--max-filesize", max_filesize])

        # Output control
        if max_count is not None:
            args.extend(["-m", str(max_count)])

        # Performance
        if threads is not None:
            args.extend(["-j", str(threads)])

        # Pattern and paths (-- to prevent pattern being treated as flag)
        args.append("--")
        args.append(pattern)
        args.extend(str(p) for p in self._ensure_list(path))

        return args

    def _execute_streaming(self, args: List[str], parser) -> Iterator:
        """Execute command and stream parsed results."""
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            for line in proc.stdout:
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("type")
                if msg_type == "match":
                    yield parser(data)
                elif msg_type == "begin" or msg_type == "end":
                    # File begin/end markers, skip
                    continue
                elif msg_type == "context":
                    # Context lines, skip (could be yielded if needed)
                    continue
                elif msg_type == "summary":
                    # Search complete
                    continue

            proc.wait()
            self._check_return_code(proc)

        except:
            proc.kill()
            raise

    def _check_return_code(self, proc: subprocess.Popen) -> None:
        """Check process return code and raise appropriate errors."""
        if proc.returncode == 0:
            return  # Success, matches found
        elif proc.returncode == 1:
            return  # Success, no matches (not an error)
        elif proc.returncode == 2:
            stderr = proc.stderr.read()
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")

            # Try to identify error type
            if "error parsing" in stderr.lower() or "regex" in stderr.lower():
                raise PatternError(stderr.strip())
            elif "no such file" in stderr.lower() or "not a directory" in stderr.lower():
                raise PathError("unknown", stderr.strip())
            else:
                raise RipgrepError(stderr.strip(), proc.returncode)
        else:
            stderr = proc.stderr.read()
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            raise RipgrepError(f"Unexpected exit code {proc.returncode}: {stderr}")

    @staticmethod
    def _ensure_list(value):
        """Ensure value is a list."""
        if isinstance(value, (list, tuple)):
            return value
        return [value]


class AsyncRipgrep:
    """Asynchronous ripgrep client.

    This client uses asyncio subprocess for non-blocking I/O,
    suitable for use in async applications.

    Example:
        >>> rg = AsyncRipgrep()
        >>> async for match in rg.search("TODO", "src/"):
        ...     print(f"{match.path}:{match.line_number}")

        >>> # With timeout
        >>> async with asyncio.timeout(5.0):
        ...     async for match in rg.search("pattern", "large_dir"):
        ...         process(match)
    """

    def __init__(self, binary: str = "rg"):
        """Initialize async ripgrep client.

        Args:
            binary: Path to ripgrep binary, or just "rg" to find in PATH.

        Raises:
            BinaryNotFoundError: If ripgrep binary is not found.
        """
        self.binary = binary
        self._binary_path = shutil.which(binary)
        if self._binary_path is None:
            raise BinaryNotFoundError(binary)

    async def search(
        self,
        pattern: str,
        path: Union[PathLike, List[PathLike]] = ".",
        **kwargs,
    ) -> AsyncIterator[Match]:
        """Search for pattern in files asynchronously.

        Same arguments as Ripgrep.search().

        Yields:
            Match objects for each match found.
        """
        # Reuse sync client's arg building
        sync_client = Ripgrep.__new__(Ripgrep)
        sync_client._binary_path = self._binary_path
        args = sync_client._build_args(
            pattern=pattern,
            path=path,
            json_output=True,
            **kwargs,
        )

        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            async for line in proc.stdout:
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if data.get("type") == "match":
                    yield Match.from_json(data)

            await proc.wait()
            await self._check_return_code(proc)

        except:
            proc.kill()
            raise

    async def search_files(
        self,
        pattern: str,
        path: Union[PathLike, List[PathLike]] = ".",
        **kwargs,
    ) -> AsyncIterator[Path]:
        """Search and return only matching file paths asynchronously."""
        sync_client = Ripgrep.__new__(Ripgrep)
        sync_client._binary_path = self._binary_path
        args = sync_client._build_args(
            pattern=pattern,
            path=path,
            files_with_matches=True,
            json_output=True,
            **kwargs,
        )

        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            async for line in proc.stdout:
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if data.get("type") == "match":
                    yield Path(data["data"]["path"]["text"])

            await proc.wait()
            await self._check_return_code(proc)

        except:
            proc.kill()
            raise

    async def _check_return_code(self, proc) -> None:
        """Check process return code and raise appropriate errors."""
        if proc.returncode in (0, 1):
            return  # Success

        stderr = await proc.stderr.read()
        stderr_str = stderr.decode("utf-8", errors="replace")

        if proc.returncode == 2:
            if "error parsing" in stderr_str.lower():
                raise PatternError(stderr_str.strip())
            raise RipgrepError(stderr_str.strip(), proc.returncode)
        else:
            raise RipgrepError(
                f"Unexpected exit code {proc.returncode}: {stderr_str}",
                proc.returncode
            )
