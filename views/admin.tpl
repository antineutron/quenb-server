<html>
  <head><title>QuenB admin interface</title></head>
  <body>
    <script src='http://code.jquery.com/jquery-1.9.1.js'></script>
    <script src='http://code.jquery.com/ui/1.10.3/jquery-ui.js'></script>
    <link rel='stylesheet' href='http://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css'>
    <link rel="stylesheet" href="http://netdna.bootstrapcdn.com/bootstrap/3.0.2/css/bootstrap.min.css">
    <script src="http://netdna.bootstrapcdn.com/bootstrap/3.0.2/js/bootstrap.min.js"></script>
 
    <div class="navbar navbar-inverse navbar-fixed-top" role="navigation">
      <div class="container">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle" data-toggle="collapse" data-target=".navbar-collapse">
            <span class="sr-only">Toggle navigation</span>
          </button>
          <a class="navbar-brand" href="#">QuenB Admin</a>
        </div>
        <div class="navbar-collapse collapse">
		  <ul class="nav navbar-nav">
            <li class="active"><a href="/admin/rules">Rules</a></li>
            <li class="active"><a href="/admin/actions">Actions</a></li>
            <li><a href="/about">About</a></li>
          </ul>
          <form class="navbar-form navbar-right" method="POST" action="/logout">
            <button type="submit" class="btn btn-success">Sign out</button>
          </form>
        </div><!--/.navbar-collapse -->
      </div>
    </div>
 
    <div class="jumbotron">
      <div class="container">
        <h1>Welcome to QuenB!</h1>
        <p>Use this interface to set rules and actions for your signage displays.</p>
      </div>
    </div>
 
    <div class="center">
	  <h2>Recently-seen client displays</h2>
	  <table>
	    <tr><th>Client ID</th><th>Hostname</th><th>IP</th><th>MAC</th><th>Actions</th></tr>

	    % for client in clients:
		<tr>
		  <td>{{client.get('cid')}}</td>
		  <td>{{client.get('hostname')}}</td>
		  <td>{{client.get('ip')}}</td>
		  <td>{{client.get('mac')}}</td>
		  <td>
		    Restart client
			Block client
			Create client rule
		  </td>
		</tr>
		% end
	  </table>
    </div>
 
    <footer>
      <p>Original system code by Jack Edge</p>
      <p>Web interface (and some tidying up) by Andy Newton</p>
      <p>Like almost everything else, this site uses Bootstrap to make it look like Twitter for no good reason.</p>
    </footer>
 
  </body>
</html>

