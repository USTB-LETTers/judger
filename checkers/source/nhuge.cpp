#include "testlib.h"

#include <string>

using namespace std;

pattern pnum("0|-?[1-9][0-9]*");

bool isNumeric(const string& p)
{
    return pnum.matches(p);
}

int main(int argc, char * argv[])
{
    setName("compare ordered sequences of two signed huge integers");
    registerTestlibCmd(argc, argv);
    
    int n = 0;
    string firstElems;

    while (!ans.seekEof() && !ouf.seekEof())
    {
        n++;
		string ja = ans.readWord();
		string pa = ouf.readWord();

		if (!isNumeric(ja))
		    quitf(_fail, "%s is not a valid integer", compress(ja).c_str());
		
		if (!isNumeric(pa))
        	quitf(_pe, "%s is not a valid integer", compress(pa).c_str());
        
		if (ja != pa)
		    quitf(_wa, "%d%s numbers differ - expected '%s', found '%s'",n , englishEnding(n).c_str(), compress(ja).c_str(), compress(pa).c_str());
        else
            if (n <= 1) firstElems += ja;
    }

    int extraInAnsCount = 0;

    while (!ans.seekEof())
    {
        ans.readLong();
        extraInAnsCount++;
    }
    
    int extraInOufCount = 0;

    while (!ouf.seekEof())
    {
        ouf.readLong();
        extraInOufCount++;
    }

    if (extraInAnsCount > 0)
        quitf(_wa, "Answer contains longer sequence [length = %d], but output contains %d elements", n + extraInAnsCount, n);
    
    if (extraInOufCount > 0)
        quitf(_wa, "Output contains longer sequence [length = %d], but answer contains %d elements", n + extraInOufCount, n);
    
    if (n == 1)
        quitf(_ok, "%d number: \"%s\"", n, compress(firstElems).c_str());
    else
        quitf(_ok, "%d numbers", n);
}
