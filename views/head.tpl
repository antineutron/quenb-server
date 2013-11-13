<html>
  <head><title>QuenB admin interface</title></head>
  <body>
    <script src='/static/js/jquery-1.9.1.js'></script>
    <script src='/static/js/jquery-ui.js'></script>
	<script src='/static/js/jquery.dataTables.min.js'></script>
    <script src="/static/js/jquery.jeditable.mini.js"></script>
    <script src="/static/js/bootstrap.min.js"></script>

    <link rel='stylesheet' href='/static/js/jquery-ui.css'>
    <link rel="stylesheet" href="/static/js/bootstrap.min.css">
	<link rel="stylesheet" href="/static/js/jquery.dataTables.css">
 
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
 
