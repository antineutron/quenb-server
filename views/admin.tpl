 % include head.tpl
    <div class="jumbotron">
      <div class="container">
        <h1>Welcome to QuenB!</h1>
        <p>Use this interface to set rules and actions for your signage displays.</p>
      </div>
    </div>
 
    <div class="center">
	  <h2>Recently-seen client displays</h2>
	  <table class="table table-striped table-bordered table-condensed">
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
 
 % include tail.tpl
