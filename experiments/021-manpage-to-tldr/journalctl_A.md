# journalctl

> Print log entries from the systemd journal.
> More information: <https://www.freedesktop.org/wiki/index.php/journalctl>

- `journalctl`: Show the contents of the journal accessible to the calling user.
 
- `journalctl --system`: Show messages from system services and the kernel.
 
- `journalctl --user <username>`: Show messages from the service of current user.
 
- `journalctl --system -u <service>`: Show messages from system services.
 
- `journalctl -n <service>`: Show messages for the service.
 
- `journalctl -u <service>`: Show messages for the service.
 
- `journalctl --system -M <container_name>`: Show messages from a running, local container.
 
- `journalctl -m` : Show entries interleaved from all available journals.
 
- `journalctl --user -D <dir>`: Show messages from the specified journal directory.
 
- `journalctl -i <glob>`: Show messages from the specified journal files matching GLOB.
