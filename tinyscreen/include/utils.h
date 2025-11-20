#ifndef UTILS_H
#define UTILS_H

#include "TinyScreen.h"

// Declarations for utils.cpp
template <typename... Args>
void serialf(const char *fmt, Args... args);
void debug_msg(char *msg, TinyScreen &display);
void hexdump(char *buf, int size);
const char* ip_to_str(IPAddress ip);
void read_line(char *buffer, int maxLen);

#endif // UTILS_H
