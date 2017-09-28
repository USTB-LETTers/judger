#include "testlib.h"
#include <stdio.h>
#include <math.h>

const double EPS = 1E-4;

int main(int argc, char * argv[])
{
    setName("compare two doubles, maximal absolute or relative error = %.5f", EPS);
    registerTestlibCmd(argc, argv);
    
    double ja = ans.readDouble();
    double pa = ouf.readDouble();
    
    if (!doubleCompare(ja, pa, EPS))
        quitf(_wa, "expected %.5f, found %.5f", ja, pa);
    
    quitf(_ok, "answer is %.5f", ja);
}
