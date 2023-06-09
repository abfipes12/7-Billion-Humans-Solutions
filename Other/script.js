
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

    let cond = new Sol_conditions();
    cond.glitches = false;
    cond.s_rate = 99;

    let bests_db = generate_bests(sol_db, cond);

    let main_table = document.getElementById("main-table");
    for (let id in bests_db)
    {
        let tr = new Tr_Data();

        tr.id = id;
        tr.name = sol_db[id].name;
        tr.ch_size = sol_db[id].ch_size;
        tr.best_size = bests_db[id].size;

        tr.ch_speed = sol_db[id].ch_speed;
        tr.best_speed = bests_db[id].speed;
        tr.sps = bests_db[id].sps;

        main_table.appendChild(create_tr(tr));
    }
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

    const size_speed_re = /(?<=>.*)[0-9]+/g;
    sol_data.size = tds[2].match(size_speed_re)[0];
    sol_data.size = parseFloat(sol_data.size);

    sol_data.speed = tds[3].match(size_speed_re);
    sol_data.speed = sol_data.speed.map(x => parseFloat(x));

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

function Best_Solutions() {
    this.size;
    this.speed;

    this.sps = [];
}

function Sol_conditions() {
    this.glitches;
    this.s_rate;
}

function generate_bests(db, sol_conditions) {
    let bests = {};

    for (let id in db) {
        let b_sol = new Best_Solutions();

        if (db[id].coffee == true) {
            continue;
        }

        b_sol.size = best_size(db[id].solutions, sol_conditions);
        b_sol.speed = best_speed(db[id].solutions, sol_conditions);
        b_sol.sps = is_sps(db[id], sol_conditions);

        bests[id] = b_sol;
    }

    return bests;
}

function is_sol_passes(sol, sol_conditions) {
    if (sol.glitches && !sol_conditions.glitches)
        return false;

    if (sol.s_rate < sol_conditions.s_rate)
        return false;

    return true;
}

function best_size(sols, sol_conditions) {
    let b_size = Infinity;
    for (let sol of sols) {
        if (!is_sol_passes(sol, sol_conditions))
            continue;

        b_size = Math.min(b_size, sol.size);
    }

    return b_size;
}

function best_speed(sols, sol_conditions) {
    let b_speed = Infinity;
    for (let sol of sols) {
        if (!is_sol_passes(sol, sol_conditions))
            continue;

        b_speed = Math.min(b_speed, ...sol.speed);
    }

    return b_speed;
}

function is_sps(year, sol_conditions) {
    let sps = [false, false];

    for (let sol of year.solutions) {
        if (!is_sol_passes(sol, sol_conditions))
            continue;

        if (sol.size > year.ch_size)
            continue;
        if (Math.min(...sol.speed) > year.ch_speed)
            continue;
        if (sol.glitches) {
            sps = [true, true];
        }
        else {
            sps = [true, false];
            break;
        }
    }
    return sps;
}

function Tr_Data() {
    this.id;
    this.name;

    this.best_size;
    this.ch_size;

    this.best_speed;
    this.ch_speed;

    this.sps = [];
}

function create_tr(tr_data) {
    const tr = document.createElement("tr");

    const year = document.createElement("td");
    const year_txt = document.createTextNode(tr_data.id);
    year.appendChild(year_txt);

    const name = document.createElement("td");
    const name_txt = document.createTextNode(tr_data.name);
    name.appendChild(name_txt);

    const size = document.createElement("td");
    const size_txt = document.createTextNode(tr_data.best_size + " / " + tr_data.ch_size);
    size.appendChild(size_txt);

    const speed = document.createElement("td");
    const speed_txt = document.createTextNode(tr_data.best_speed + " / " + tr_data.ch_speed);
    speed.appendChild(speed_txt);

    const speed_size = document.createElement("td");
    const speed_size_txt = document.createTextNode(tr_data.sps[0]);
    speed_size.appendChild(speed_size_txt);

    tr.appendChild(year);
    tr.appendChild(name);
    tr.appendChild(size);
    tr.appendChild(speed);
    tr.appendChild(speed_size);

    return tr;
}
