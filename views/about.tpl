% include head.tpl current_user=current_user

    <style>
	.panel-title{
		text-align: center;
	}
	</style>
    <div class="jumbotron">
      <div class="container">
        <h1>About QuenB</h1>
		<p>
		  QuenB is a digital signage system designed to be used on the <a href='http://www.raspberrypi.org'>Raspberry Pi</a> single-board computer. What does this mean? Well, it means you can take an old monitor, spend a few quid on a RasPi, and turn it into a digital display for your foyer! (or equally you can buy a huge TV and a desktop PC to achieve a more impressive result for more money, it's up to you).
		</p>
      </div>
    </div>

	<div class="container">
	  <div class="row">
		<div class='col-md-4 panel-heading'>
		  <h3 class='panel-title'>What</h3>
		  QuenB is a client/server system: the client is a web browser, ideally running full-screen (midori on the RasPi works nicely); the client requests a single 'webclient' page, with some client-side javascript code, from the backend server, and then periodically asks the server "what should I display?". The server is pretty lightweight and can run on the same Pi as the client, on another Pi, or on some other suitable computer - it just needs to be web accessible by the cleint.
		</div>

		<div class='col-md-4 panel-heading'>
		  <h3 class='panel-title'>Who</h3>
		  QuenB was originally written as a project by Jack Edge, a student in <a href='http://www.ecs.soton.ac.uk'>Electronics and Computer Science</a> at the University of Southampton. The admin interface and some general tidying up was done by Andy Newton.
		</div>

		<div class='col-md-4 panel-heading'>
		  <h3 class='panel-title'>How</h3>
		  QuenB is primarily written in the <a href='http://www.python.org'>Python</a> programming language, with some JavaScript client-side code. It can display static images or complete webpages (NB some pages such as youtube refuse to display in an iframe, which will currently not work with QuenB). 
		</div>

      </div>
    </div>

	<div class="container">
	  <div class="row">
		<div class='col-md-4 col-md-offset-4 panel-heading'>
		<h3 class='panel-title'>Open source!</h3>
		We use the following open-source projects:
		<ul>
		  <li>The <a href='http://bottlepy.org'>Bottle</a> Python web framework</li>
		  <li>The awesome <a href='http://jquery.com'>jQuery</a> JavaScript library, which makes life SO much easier for everyone</li>
		  <li>The <a href='http://jqueryui.com'>jQuery UI</a> and <a href='http://getbootstrap.com'>Bootstrap</a> libraries for fancy-looking graphics, nice layouts etc.</li>
		  <li>The <a href='http://datatables.net'>DataTables</a> jQuery plugin for flashy sortable/searchable/editable table layouts all over the admin interface</li>
		</ul>
		Thanks, everyone!
		</div>
      </div>
    </div>


% include tail.tpl
