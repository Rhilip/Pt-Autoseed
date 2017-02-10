jQuery(document).ready(function($) {

    /* ======= Scrollspy ======= */
    $('body').scrollspy({ target: '#header', offset: 400});
    
    /* ======= Fixed header when scrolled ======= */
    
    $(window).bind('scroll', function() {
         if ($(window).scrollTop() > 50) {
             $('#header').addClass('navbar-fixed-top');
         }
         else {
             $('#header').removeClass('navbar-fixed-top');
         }
    });
   
    /* ======= ScrollTo ======= */
    $('a.scrollto').on('click', function(e){
        
        //store hash
        var target = this.hash;
                
        e.preventDefault();
        
		$('body').scrollTo(target, 800, {offset: -70, 'axis':'y', easing:'easeOutQuad'});
        //Collapse mobile menu after clicking
		if ($('.navbar-collapse').hasClass('in')){
			$('.navbar-collapse').removeClass('in').addClass('collapse');
		}
		
	});

    /* ======= Update info ======= */
    function timechange(time) {
        var change_time = parseInt(time);
        var date = new Date(change_time * 1000);
        return date.toLocaleString()
    }

    function update_info() {
        $.getJSON("/tostatus.json", function (data) {
            console.log("Get data success!");
            $("#last_update_time").text(data.last_update_time);  // 更新时间戳
            var status_table = $("#status_table");
            var output_main = "<thead><tr><th>#</th><th class=\"text-center\">Title</th><th>Size</th><th>Started At</th><th>Download Status</th><th>Seed Status</th></tr></thead><tbody>";
            for (var i = 0, l = data.data.length; i < l; i++) {
                var status = data.data[i][1];
                var output = "<tr>" +
                    "<td>" + data.data[i][0] + "</td>" +
                    "<td>" + status["title"] + "</td>" +
                    "<td>" + status["size"] + "</td>" +
                    "<td>" + timechange(status["download_start_time"]) + "</td>" +
                    "<td>" + status["download_status"] + " R:" + status["download_upload_ratio"] + "</td>" +
                    "<td>" + status["reseed_status"] + " R:" + status["reseed_ratio"] + "</td>" +
                    "</tr>";
                output_main = output_main.concat(output);
                if (i>=10){
                    break;
                }
            }
            output_main = output_main.concat("</tbody>");
            status_table.html(output_main);
        })
    }

    self.setInterval(update_info(),60000);
});