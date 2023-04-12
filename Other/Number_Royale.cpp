// by @abfipes12, code for finding best number combination for Year 22 +50%

#include <iostream>
#include <random>

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

	// Create a random cube generator
	std::uniform_int_distribution cube{ 0, 99 };

	// Store solution with most succesful runs
    Solution best_sol {0,0,0};
    
    constexpr int runs_num { 100'000 }; // oryginal was tested on 1'000'000
    // 100'000 runs under 1 minute

	for (int first = 50 ; first < 100; ++first)
    {
        for (int second = first; second < 100; ++second)
        {
            int succeses = 0;
            for (int runs = 0; runs < runs_num; ++runs)
            {
                int surv_first = 0;
                int surv_second = 0;
                for (int i = 0; i < 10; ++i)
                {
                    int worker = cube(mt);
                    if (worker >= first)
                        ++surv_first;

                    if (worker >= second)
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