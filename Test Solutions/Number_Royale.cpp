// by @abfipes12, code to find the best combination of numbers for the year 22 +50%

#include <iostream>
#include <random>
#include <array>
#include <algorithm>

struct Solution
{
    int succeses;
    int first;
    int second;
};

int main()
{
	std::random_device rd;
	std::seed_seq ss{ rd(), rd(), rd(), rd(), rd(), rd(), rd(), rd() };
	std::mt19937 mt{ ss };

	std::uniform_int_distribution cube_generator{ 0, 99 };

	// Store solution with the most successful run
    Solution best_sol {0,0,0};
    
    constexpr int runs_num { 1'000'000 };
    // 100'000 runs under 1 minute

	for (int first = 63 ; first < 100; ++first)
    {
        for (int second = first; second < 100; ++second)
        {
            int succeses = 0;
            for (int runs = 0; runs < runs_num; ++runs)
            {
                int surv_first = 0;
                int surv_second = 0;
                std::array<int, 10> workers;
                std::generate(workers.begin(), workers.end(), [&](){ return cube_generator(mt);});
                for (int i = 0; i < workers.size(); ++i)
                {
                    if (i != 0)
                    {
                        if (workers[i] < workers[i - 1])
                            continue;
                    }

                    if (i != workers.size() - 1)
                    {
                        if (workers[i] < workers[i + 1])
                            continue;
                    }

                    if (workers[i] >= first)
                        ++surv_first;

                    if (workers[i] >= second)
                        ++surv_second;
                }

                if (surv_first == 1 || surv_second == 1)
                    ++succeses;
            }

            if (succeses > best_sol.succeses)
                best_sol = {succeses,first,second};
        }
    }
	
    std::cout << "Best solution: " << (double)best_sol.succeses / runs_num * 100 << "% " << best_sol.first << ' ' << best_sol.second;

	return 0;
}