// Minimal F2 OCL register driver for the DNHacks matrix-vector experiment.
// Build on an AWS FPGA Developer AMI after sourcing sdk_setup.sh.

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "fpga_mgmt.h"
#include "fpga_pci.h"
#include "hal/fpga_common.h"

#define ROWS 8
#define COLS 8
#define VECTORS 32
#define MAX_POLLS 1000

#define REG_WEIGHT(i) (0x000u + 4u * (unsigned)(i))
#define REG_INPUT(i)  (0x100u + 4u * (unsigned)(i))
#define REG_CONTROL   0x120u
#define REG_STATUS    0x124u
#define REG_OUTPUT(i) (0x200u + 4u * (unsigned)(i))

static int load_csv(const char *path, int rows, int cols, int data[rows][cols]) {
    FILE *fp = fopen(path, "r");
    if (!fp) {
        perror(path);
        return -1;
    }
    for (int r = 0; r < rows; ++r) {
        for (int c = 0; c < cols; ++c) {
            if (fscanf(fp, " %d", &data[r][c]) != 1) {
                fprintf(stderr, "Malformed CSV %s at row %d column %d\n", path, r, c);
                fclose(fp);
                return -1;
            }
            if (c + 1 < cols && fgetc(fp) != ',') {
                fprintf(stderr, "Malformed CSV separator in %s at row %d column %d\n", path, r, c);
                fclose(fp);
                return -1;
            }
        }
        int ch;
        while ((ch = fgetc(fp)) != '\n' && ch != EOF) {}
    }
    fclose(fp);
    return 0;
}

static int signed24(uint32_t value) {
    value &= 0x00ffffffu;
    return (value & 0x00800000u) ? (int)(value | 0xff000000u) : (int)value;
}

static int write_reg(pci_bar_handle_t bar, uint32_t addr, uint32_t value) {
    int rc = fpga_pci_poke(bar, addr, value);
    if (rc) fprintf(stderr, "poke 0x%03x failed: %d\n", addr, rc);
    return rc;
}

static int read_reg(pci_bar_handle_t bar, uint32_t addr, uint32_t *value) {
    int rc = fpga_pci_peek(bar, addr, value);
    if (rc) fprintf(stderr, "peek 0x%03x failed: %d\n", addr, rc);
    return rc;
}

int main(int argc, char **argv) {
    const char *design = argc > 1 ? argv[1] : "generic";
    int slot = argc > 2 ? atoi(argv[2]) : 0;
    const char *weights_path = argc > 3 ? argv[3] : "models/weights.csv";
    const char *inputs_path = argc > 4 ? argv[4] : "models/inputs.csv";
    const char *expected_path = argc > 5 ? argv[5] : "models/expected_outputs.csv";
    int fixed = strcmp(design, "fixed") == 0;
    int weights[ROWS][COLS], inputs[VECTORS][COLS], expected[VECTORS][ROWS];
    pci_bar_handle_t bar = PCI_BAR_HANDLE_INIT;
    int rc = 0;

    if (!fixed && strcmp(design, "generic") != 0) {
        fprintf(stderr, "design must be generic or fixed\n");
        return 2;
    }
    if (load_csv(weights_path, ROWS, COLS, weights) ||
        load_csv(inputs_path, VECTORS, COLS, inputs) ||
        load_csv(expected_path, VECTORS, ROWS, expected)) return 2;

    rc = fpga_mgmt_init();
    if (rc) {
        fprintf(stderr, "fpga_mgmt_init failed: %d\n", rc);
        return rc;
    }
    rc = fpga_pci_attach(slot, FPGA_APP_PF, APP_PF_BAR0, 0, &bar);
    if (rc) {
        fprintf(stderr, "fpga_pci_attach failed for slot %d: %d\n", slot, rc);
        fpga_mgmt_close();
        return rc;
    }

    for (int v = 0; v < VECTORS && !rc; ++v) {
        if (!fixed) {
            for (int r = 0; r < ROWS && !rc; ++r)
                for (int c = 0; c < COLS && !rc; ++c)
                    rc = write_reg(bar, REG_WEIGHT(r * COLS + c), (uint8_t)weights[r][c]);
        }
        for (int c = 0; c < COLS && !rc; ++c)
            rc = write_reg(bar, REG_INPUT(c), (uint8_t)inputs[v][c]);
        usleep(1000);
        if (!rc) rc = write_reg(bar, REG_CONTROL, 0x3u);

        uint32_t status = 0;
        int polls = 0;
        while (!rc && !(status & 1u) && polls++ < MAX_POLLS) {
            rc = read_reg(bar, REG_STATUS, &status);
            if (!rc && !(status & 1u)) usleep(1000);
        }
        if (!rc && !(status & 1u)) {
            fprintf(stderr, "timeout waiting for done on vector %d\n", v);
            rc = 1;
        }
        for (int r = 0; r < ROWS && !rc; ++r) {
            uint32_t raw = 0;
            rc = read_reg(bar, REG_OUTPUT(r), &raw);
            if (!rc && signed24(raw) != expected[v][r]) {
                fprintf(stderr, "FAIL design=%s vector=%d output=%d expected=%d observed=%d\n",
                        design, v, r, expected[v][r], signed24(raw));
                rc = 1;
            }
        }
        if (!rc) rc = write_reg(bar, REG_CONTROL, 0x2u);
    }

    if (!rc) printf("PASS design=%s vectors=%d outputs=%d\n", design, VECTORS, VECTORS * ROWS);
    fpga_pci_detach(bar);
    fpga_mgmt_close();
    return rc;
}
