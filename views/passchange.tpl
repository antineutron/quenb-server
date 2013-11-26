 % include head.tpl current_user=current_user
  <h2>Change password</h2>

  <p>You are logged in as {{current_user.username}}</p>

  <form class="well" action="/admin/password_reset" method="POST">
      <fieldset>
        <label for='passcurrent'>Enter your current password:</label>
        <input type='password' name='passcurrent'/>
        <label for='passnew'>Enter a new password:</label>
        <input type='password' name='passnew'/>
        <label for='passconfirm'>Confirm your new password:</label>
        <input type='password' name='passconfirm'/>
		<input type='submit' value='Change password'/>
	  </fieldset>
  </form>
</div>

% include tail.tpl
