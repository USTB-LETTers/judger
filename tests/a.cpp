/*
* Filename:    a.cpp
* Created:     Sunday, September 24, 2017 03:13:09 PM
* Author:      crazyX
* More:
*
*/
#include <bits/stdc++.h>

#define mp make_pair
#define pb push_back
#define fi first
#define se second
#define SZ(x) ((int) (x).size())
#define all(x) (x).begin(), (x).end()
#define sqr(x) ((x) * (x))
#define clr(a,b) (memset(a,b,sizeof(a)))
#define y0 y3487465
#define y1 y8687969
#define fastio std::ios::sync_with_stdio(false)

using namespace std;

typedef long long ll;

const int INF = 1e9 + 7;
const int maxn = 1e7 + 7;
int a[maxn];

int n, m, cnt;

int main()
{
#ifdef AC
	freopen("2.in", "r", stdin);
	freopen("2.out", "w", stdout);
#endif
	for (int i = 0; i < maxn; i += 1) a[i] = i;
	while (scanf("%d%d", &a[cnt], &a[cnt + 1]) != EOF) {
		printf("%d\n", a[cnt] + a[cnt + 1]);
		cnt++;
	}
	return 0;
}
