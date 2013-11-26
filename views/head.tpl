<html>
  <head><title>QuenB admin interface</title></head>
  <body>
    <script src='/static/js/jquery-1.9.1.js'></script>
    <script src='/static/js/jquery-ui.js'></script>
	<script src='/static/js/jquery.dataTables.min.js'></script>
    <script src="/static/js/jquery.jeditable.mini.js"></script>
    <script src="/static/js/bootstrap.min.js"></script>
    <script src="/static/js/noty/jquery.noty.js"></script>
    <script src="/static/js/noty/layouts/all.js"></script>
    <script src="/static/js/noty/themes/default.js"></script>

    <link rel='stylesheet' href='/static/js/jquery-ui.css'>
    <link rel="stylesheet" href="/static/js/bootstrap-cerulean.min.css">
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
		  	% setdefault('nav_selected', '')
            <li><a href="/admin/rules">Rules</a></li>
            <li><a href="/admin/actions">Actions</a></li>
            <li><a href="/webclient">Client View</a></li>
            <li><a href="/about">About</a></li>
          </ul>
		  % if defined('current_user') and current_user:
          <form class="navbar-form navbar-right" method="POST" action="/logout">
		    <strong>Logged in as {{current_user.username}}</strong>
		     <div class="form-group">
            <button type="submit" class="btn btn-success">Sign out</button>
			<em><a href='/admin/password_reset'>Change password</a></em>>
			</div>
          </form>
		  % else:
          <form class="navbar-form navbar-right" method="POST" action="/login">
		     <div class="form-group">
		    <input name="username" type="text" placeholder="Admin username" class="form-control">
			</div>
		     <div class="form-group">
			<input name="password" type="password" placeholder="Password" class="form-control">
			</div>
            <button type="submit" class="btn btn-success">Sign in</button>
          </form>
		  % end if
        </div><!--/.navbar-collapse -->
      </div>
    </div>
 
