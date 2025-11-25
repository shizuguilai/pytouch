#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>

typedef int (*orig_execve_f_type)(const char *, char *const[], char *const[]);

static const char *PIPE = "/tmp/terminal_capture.pipe";

int execve(const char *filename, char *const argv[], char *const envp[]) {
    orig_execve_f_type orig_execve;
    orig_execve = (orig_execve_f_type)dlsym(RTLD_NEXT, "execve");

    // 只要是终端内部运行的命令，一律重定向 stdout
    // 不管是不是 test.sh
    int fd = open(PIPE, O_WRONLY | O_APPEND);
    if (fd != -1) {
        dup2(fd, 1);  // stdout → pipe
        dup2(fd, 2);  // stderr → pipe
        close(fd);
    }

    return orig_execve(filename, argv, envp);
}
