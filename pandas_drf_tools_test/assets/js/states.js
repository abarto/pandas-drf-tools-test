$(function() {
    var $svg = $('svg');
    var svg = d3.select("svg"),
        margin = {top: 20, right: 20, bottom: 30, left: 40},
        width = +$svg.width() - margin.left - margin.right,
        height = +$svg.height() - margin.top - margin.bottom;

    var tip = d3.tip()
        .attr('class', 'd3-tip').html(function(d) {
            return "<div><span class=\"tooltip-title\">" + d.STNAME + "</span><br/>" +
                "Population:&nbsp;" + d.TOT_POP +
                " (M: " + d.TOT_MALE + ", F: " + d.TOT_FEMALE + ")" +
                "</div>";
        });
    svg.call(tip);

    var x = d3.scaleBand().rangeRound([0, width]).padding(0.1),
        y = d3.scaleLinear().rangeRound([height, 0]);

    var xAxis = d3.axisBottom(x);
    var yAxis = d3.axisLeft(y)
        .tickFormat(d3.format(".2s"));

    var g = svg.append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    d3.json("/api/states/", function(error, data) {
        if (error) throw error;

        data = data.records;

        x.domain(data.map(function(d) { return d.STUSAB; }));
        y.domain([0, d3.max(data, function(d) { return +d.TOT_POP; })]);

        g.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis);

        g.append("g")
            .attr("class", "y axis")
            .call(yAxis)

        g.selectAll(".bar")
            .data(data)
            .enter().append("rect")
                .attr("class", "bar")
                .attr("x", function(d) { return x(d.STUSAB); })
                .attr("y", function(d) { return y(d.TOT_POP); })
                .attr("width", x.bandwidth())
                .attr("height", function(d) { return height - y(d.TOT_POP); })
                .on("mouseover", tip.show)
                .on("mouseout", tip.hide)
                .on("click", function(d) {
                    window.location.assign("/counties/" + d.STATE + "/");
                });

        g.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", "0.75em")
            .attr("text-anchor", "end")
            .text("Population");
    });
});