
function readGitHubFile() {
    let fileUrl = 'https://raw.githubusercontent.com/abfipes12/7-Billion-Humans-Solutions/main/README.MD';

    fetch(fileUrl)
        .then(response => response.text())
        .then(text => {
            main(text);
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function main(raw_readme) {
    let sol_db = build_db(raw_readme);

    console.log(sol_db);
}

function to_raw_years(raw_readme) {
    let solutions_md = raw_readme.split('---', 2)[1];

    return solutions_md.split('###').slice(1);
}

function build_db(raw_readme) {
    let db = {
        "01": { "coffee": true, name: "You're Hired!", id: "01" },
        "08": { "coffee": true, name: "Intro to Moral Officers", id: "08" },
        "27": { "coffee": true, name: "Fitness Program", id: "27" },
        "45": { "coffee": true, name: "Morning Petroleum", id: "45" },
    };

    let raw_years = to_raw_years(raw_readme);

    for (let raw_year of raw_years) {
        let year_data = year_parser(raw_year);
        
        db[year_data.id] = year_data;
    }

    return db;
}

function Year_data() {
    this.id;
    this.name;
    this.coffee;
    this.solutions = [];

    this.ch_size;
    this.ch_speed;
}

function year_parser(raw_year) {
    let year_data = new Year_data();

    const year_re = /(?<=Year ).*(?= -)/;
    year_data.id = raw_year.match(year_re)[0];

    const name_re = /(?<=- )[\w|\s|,]+(?= )/;
    year_data.name = raw_year.match(name_re)[0];

    const rows_re = /(?<=<tr>).*?(?=<\/tr>)/sg;
    let raw_rows = raw_year.match(rows_re);

    let ch_row = raw_rows.shift();
    
    const max_size_re = /(?<=Size \[)\d+(?=\])/;
    year_data.ch_size = ch_row.match(max_size_re)[0];

    const max_speed_re = /(?<=Time \[)\d+(?=s\])/;
    year_data.ch_speed = ch_row.match(max_speed_re)[0];
    
    
    for (let sol_row of raw_rows) {
        year_data.solutions.push(parse_sol_rows(sol_row));
    }

    return year_data;
}

function Sol_data() {
    this.category;
    this.authors = [];

    this.size;
    this.speed = [];
    this.glitches;
    this.s_rate;

    this.link;
}

//najbardziej efektywna programista

function parse_sol_rows(sol_row) {
    let sol_data = new Sol_data();

    sol_row = sol_row.trim();
    let tds = sol_row.split("\n");

    const category_re = /(?<=\">).+(?=<\/a)/;
    sol_data.category = tds[0].match(category_re)[0];

    const authors_re = /(?<=>).+?(?=<)/g;
    sol_data.authors = tds[1].match(authors_re);

    const size_speed_re = /[0-9]+/g;
    sol_data.size = tds[2].match(size_speed_re)[0];
    sol_data.speed = tds[3].match(size_speed_re);

    sol_data.glitches = tds[0].includes('WithGliches');

    if (tds[0].includes('+50')) {
        sol_data.s_rate = 50;
    }
    else {
        sol_data.s_rate = 99;
    }

    const link_beg = 'https://raw.githubusercontent.com/abfipes12/7-Billion-Humans-Solutions/main/';
    const link_re = /(?<=href=\").+(?=\")/;
    sol_data.link = link_beg + tds[0].match(link_re);

    return sol_data;
}

function create_tr() {
    // let main_table = document.getElementById("main-table");

    const tr = document.createElement("tr");

    const year = document.createElement("td");
    const year_txt = document.createTextNode(ye);
    year.appendChild(year_txt);

    const name = document.createElement("td");
    const name_txt = document.createTextNode(na);
    name.appendChild(name_txt);

    const size = document.createElement("td");
    const size_txt = document.createTextNode(si);
    size.appendChild(size_txt);

    const speed = document.createElement("td");
    const speed_txt = document.createTextNode(sp);
    speed.appendChild(speed_txt);

    const speed_size = document.createElement("td");
    const speed_size_txt = document.createTextNode(sps);
    speed_size.appendChild(sps_txt);

    tr.appendChild(year)
    tr.appendChild(name)
    tr.appendChild(size)
    tr.appendChild(speed)
    tr.appendChild(speed_size)

    return tr;
    // main_table.appendChild(tr)
}

function Year_tr() {
    this.ye
    this.na
    this.si
    this.sp
    this.sps
}

// function year_to_md(year)
// {
//     let tr = new Year_tr();
//     tr.ye = year;
//     tr.name = solutions_db[year].name

//     let min_si = 256;
//     for (sol of solutions_db[year].solutions)
//     {
//         if (sol.)
//     }
// }

// function populate_table()
// {
//     for(year in solutions_db)
//     {
//         create_tr(
//             year,
//             solutions_db[year][name],
//             si,sp,sps)
//     }
// }