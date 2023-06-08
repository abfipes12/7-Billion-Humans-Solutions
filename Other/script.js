function readGitHubFile() {
    let fileUrl = 'https://raw.githubusercontent.com/abfipes12/7-Billion-Humans-Solutions/main/README.MD';

    fetch(fileUrl)
        .then(response => response.text())
        .then(text => {
            parse_page(text);
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

class Solution {
    category;
    authors;

    year;

    size;
    speed;
    glitches = false;
    s_rate = 99;

    link;

    constructor(solution_txt) {

        let lines = solution_txt.split('\n');

        const category_re = /\">(.+)<\/a/;
        lines[1].match()

        const autors_re = />(.+?)</g;
        lines[2].match()
        
        const year_re = /Year (.*) -/;
        lines[1].match()

        const size_re = /[0-9]+/;
        lines[3].match()

        const speed_re = /[0-9]+/g;
        lines[4].match()

        glitches = lines[1].includes('WithGliches');
        
        if (lines[1].includes('+50')) {
            s_rate = 50;
        }
        
        const link_re = /href=\"(.+)\"/;
        lines[1].match()
        let link = 'https://raw.githubusercontent.com/abfipes12/7-Billion-Humans-Solutions/main/README.MD';
    }
    //najbardziej efektywna programista
}

function parse_page(raw_page_text) {
    let solutions_md = raw_page_text.split('---', 2)[1];

    let years_arr = solutions_md.split('###').slice(1);

    const re = /<tr>(.*?)<\/tr>/gs;

    let year_solutions = years_arr[21].match(re);
    let year_year = years_arr[21].match(/Year (.*) -/);

    let lines = year_solutions[2].split('\n');
        // lines.pop();
        // lines.shift();

    console.log(lines);
    // document.querySelector("body").innerText = year_solutions;
    // porządny pierdolec podczas poprawiania pisma programu
}