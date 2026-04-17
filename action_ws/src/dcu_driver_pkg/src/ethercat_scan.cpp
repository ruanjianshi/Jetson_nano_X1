#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "ethercat.h"

void setbufunbuffered()
{
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
}

void printslave(int i)
{
    fprintf(stderr, "=== Slave %d ===\n", i);
    fprintf(stderr, "  Name: %s\n", ec_slave[i].name);
    fprintf(stderr, "  Output bits: %d\n", ec_slave[i].Obits);
    fprintf(stderr, "  Input bits: %d\n", ec_slave[i].Ibits);
    fprintf(stderr, "  State: %d\n", ec_slave[i].state);
    fprintf(stderr, "  FMMU: %d\n", ec_slave[i].FMMUunused);
    fprintf(stderr, "  SM: %d\n", ec_slave[i].SM[0].StartAddr);
}

void simpletest(const char *ifname)
{
    fprintf(stderr, "EtherCAT Bus Scan\n");
    fprintf(stderr, "Interface: %s\n\n", ifname);
    
    if (ec_init(ifname) < 0) {
        fprintf(stderr, "ERROR: Failed to init EtherCAT\n");
        return;
    }
    fprintf(stderr, "EtherCAT initialized\n");
    
    if (ec_config_init(FALSE) <= 0) {
        fprintf(stderr, "ERROR: No slaves found!\n");
        ec_close();
        return;
    }
    
    fprintf(stderr, "Found %d slave(s)\n\n", ec_slavecount);
    
    for (int i = 1; i <= ec_slavecount; i++) {
        printslave(i);
    }
    
    ec_close();
    fprintf(stderr, "\nScan complete.\n");
}

int main(int argc, char **argv)
{
    const char *ifname = "eth0";
    setbufunbuffered();
    
    if (argc > 1) ifname = argv[1];
    
    simpletest(ifname);
    return 0;
}
