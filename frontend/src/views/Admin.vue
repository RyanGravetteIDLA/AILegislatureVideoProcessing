<template>
  <div>
    <h1 class="page-title">Admin Dashboard</h1>
    <p class="page-description">Manage the Idaho Legislature Media platform</p>
    
    <div class="login-card">
      <h2 class="login-title">Access Restricted</h2>
      <p class="login-message">
        The admin dashboard requires authentication. Please log in with your administrator credentials to access this area.
      </p>
      <button class="login-button">Log In</button>
    </div>
  </div>
</template>

<style scoped>
.page-title {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
  color: #334e68;
}

.page-description {
  font-size: 1.1rem;
  color: #486581;
  margin-bottom: 2rem;
}

.login-card {
  background-color: white;
  padding: 2rem;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  text-align: center;
  max-width: 500px;
  margin: 0 auto;
}

.login-title {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 1rem;
  color: #334e68;
}

.login-message {
  color: #627d98;
  margin-bottom: 1.5rem;
}

.login-button {
  background-color: #486581;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.25rem;
  font-weight: 500;
  cursor: pointer;
  font-size: 1rem;
}

.login-button:hover {
  background-color: #334e68;
}
</style>