#!/usr/bin/python3
# Lint as: python3
"""Search and replace files recursively."""

import argparse
import functools
import os
import pathlib
import sys


NORMAL, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN = [
    "\x1b[0m"] + ["\x1b[3%dm" % i for i in range(1, 7)]


def color(c, *args, cond=True):
  s = " ".join(map(str, args))
  return c + s + NORMAL if cond else s


red, green, yellow, blue, magenta, cyan = [
    functools.partial(color, c)
    for c in [RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN]]


def gitignore(root: pathlib.PurePath):
  """Get the contents of the .gitignore file in the given directory."""
  try:
    import gitignore_parser
  except Exception as e:
    print(yellow("module 'gitignore_parser' module import failed, continuing:"),
          f"{type(e).__name__}: {e}")
  else:
    for path in (root / "foo").parents:
      if (path / ".gitignore").is_file():
        return gitignore_parser.parse_gitignore(path / ".gitignore")
      if (path / ".git").exists():
        break
  return lambda x: False


def main():
  if not os.path.isdir(os.getcwd()):
    sys.exit(f"Current working directory {os.getcwd()} is invalid.")

  parser = argparse.ArgumentParser(
      description="Search and replace files recursively.")
  parser.add_argument("-d", "--dir", default=os.getcwd(),
                      help="Where to search, defaults to the cwd.")
  parser.add_argument("-g", "--file_type", default="",
                      help="Only search files with this suffix.")
  parser.add_argument("-q", "--quiet", action="store_true",
                      help="Don't output the search results.")
  parser.add_argument("-v", "--verbose", action="store_true",
                      help="Show files being searched/skipped.")
  parser.add_argument("old", help="String to search for.")
  parser.add_argument("new", default=None, nargs="?",
                      help="What to replace it with, or skip to only search.")
  args = parser.parse_args()

  if args.old == args.new:
    print(red("new matches old, so no modifications will be made."))
    args.new = None

  searched_files = 0
  occurrences = 0
  failures = 0
  root = pathlib.Path(args.dir).resolve()
  if not root.is_dir():
    sys.exit(red("Path is not a directory:", args.dir))
  print(yellow("Searching under:"), root)

  gitignore_matches = gitignore(root)

  for subdir, _, files in sorted(root.walk()):
    for file in sorted(files):
      path = subdir / file
      short_path = path.relative_to(root)
      if gitignore_matches(short_path):
        if args.verbose:
          print(red("Skipping:"), short_path)
        continue
      if args.file_type and not path.endswith("." + args.file_type):
        if args.verbose:
          print(red("Skipping:"), short_path)
        continue
      if args.verbose:
        print(yellow("Searching:"), short_path)
      try:
        with open(path, "r") as f:
          contents = f.read()
      except IOError as e:
        print(red("Failed to read:"), short_path)
        print(e)
        failures += 1
        continue
      except UnicodeDecodeError:
        print(red("Failed to decode file as unicode:"), short_path)
        failures += 1
        continue
      count = contents.count(args.old)
      searched_files += 1
      occurrences += count
      if count:
        print(yellow("Found"), green(count),
              yellow("occurrences in:"), magenta(short_path))
        if not args.quiet:
          for i, line in enumerate(contents.split("\n"), 1):
            if args.old in line:
              print("{}:".format(cyan(i)),
                    line.replace(args.old, green(args.old)))
        if args.new is not None:
          modified = contents.replace(args.old, args.new)
          try:
            with open(path, "w") as f:
              f.write(modified)
          except IOError as e:
            print(red("Failed to write:"), short_path)
            print(e)
            failures += 1
          else:
            print(green("Modified:"), short_path)
        print()
  print(yellow("Searched"), searched_files,
        yellow("files and", ("replaced" if args.new is not None else "found")),
        occurrences, yellow("occurrences."))
  if failures:
    print(red("Failures:"), failures)


if __name__ == "__main__":
  main()