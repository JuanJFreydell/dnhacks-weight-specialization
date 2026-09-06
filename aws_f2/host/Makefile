SDK_USERSPACE_DIR := $(SDK_DIR)/userspace
INCLUDES := -I$(SDK_USERSPACE_DIR)/include
LDFLAGS := -L$(SDK_USERSPACE_DIR)/lib/so
LDLIBS := -lfpga_mgmt
CFLAGS := -std=gnu11 -O2 -Wall -Wextra -Werror $(INCLUDES)

.PHONY: all clean

all: matvec_host

matvec_host: matvec_host.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS) $(LDLIBS)

clean:
	$(RM) matvec_host
