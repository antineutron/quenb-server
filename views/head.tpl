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
          <a class="navbar-brand" href="/admin">QuenB Admin</a>
        </div>
        <div class="navbar-collapse collapse">
		  <ul class="nav navbar-nav">
            <li class="active"><a href="/admin/rules">Rules</a></li>
            <li class="active"><a href="/admin/actions">Actions</a></li>
            <li><a href="/webclient">Client view</a></li>
            <li><a href="/about">About</a></li>
          </ul>
          <form class="navbar-form navbar-right" method="POST" action="/logout">
            <button type="submit" class="btn btn-success">Sign out</button>
          </form>
        </div><!--/.navbar-collapse -->
      </div>
    </div>
 
