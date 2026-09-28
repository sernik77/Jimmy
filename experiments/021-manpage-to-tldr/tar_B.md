# tar

> The 'tar' command is a powerful archiving tool that stores and retrieves files to and from a single file, providing vari
> More information: <https://www.gnu.org/software/tar/manual>.

- Create an archive:

`tar -czf {{archive.tar}}`

- Extract a file from an archive:

`tar -xvf {{archive.tar}} {{file.tar}}`

- List the contents of an archive:

`tar -tvf {{archive.tar}}`

- Archive a file:

`tar -cf {{archive.tar}} {{file.tar}}`

- List the contents with verbose mode:

`tar -v -f {{archive.tar}}`

- Create an incremental archive:

`tar -c --old-archive {{archive.tar}}`
