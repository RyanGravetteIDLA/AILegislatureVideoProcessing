<script setup>
// Simplified Home page that doesn't rely on the store
</script>

<template>
  <div>
    <div class="hero">
      <h1 class="hero-title">Legislative Video Reviews with AI</h1>
      <p class="hero-description">Browse and search through Idaho legislative session videos, audio recordings, and transcripts processed with advanced AI technology.</p>
      
      <div class="hero-actions">
        <router-link to="/videos" class="btn btn-primary">Explore Videos</router-link>
        <router-link to="/audio" class="btn btn-secondary">Browse Audio</router-link>
        <router-link to="/transcripts" class="btn btn-secondary">View Transcripts</router-link>
      </div>
    </div>
    
    <!-- Stats cards -->
    <div class="stats-grid">
      <div class="stats-card">
        <h3>Total Videos</h3>
        <p class="stat">125</p>
      </div>
      <div class="stats-card">
        <h3>Total Audio Files</h3>
        <p class="stat">142</p>
      </div>
      <div class="stats-card">
        <h3>Total Transcripts</h3>
        <p class="stat">98</p>
      </div>
      <div class="stats-card">
        <h3>Processed Today</h3>
        <p class="stat">12</p>
      </div>
    </div>
    
    <!-- Quick access -->
    <h2 class="section-title">Quick Access</h2>
    <div class="quick-access-grid">
      <router-link to="/videos" class="quick-access-card">
        <h3>Video Library</h3>
        <p>Browse all legislative session videos</p>
      </router-link>
      <router-link to="/audio" class="quick-access-card">
        <h3>Audio Library</h3>
        <p>Browse all legislative session audio recordings</p>
      </router-link>
      <router-link to="/transcripts" class="quick-access-card">
        <h3>Transcript Library</h3>
        <p>Browse all legislative session transcripts</p>
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.hero {
  background-color: #f8f9fa;
  padding: 2rem;
  border-radius: 0.5rem;
  margin-bottom: 2rem;
  text-align: center;
}

.hero-title {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 1rem;
  color: #334e68;
}

.hero-description {
  font-size: 1.1rem;
  color: #486581;
  margin-bottom: 1.5rem;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.hero-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stats-card {
  background-color: white;
  padding: 1.5rem;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.stats-card h3 {
  font-size: 0.9rem;
  color: #627d98;
  margin-bottom: 0.5rem;
}

.stat {
  font-size: 2rem;
  font-weight: bold;
  color: #334e68;
}

.section-title {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 1rem;
  margin-top: 2rem;
  color: #334e68;
}

.quick-access-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.quick-access-card {
  background-color: white;
  padding: 1.5rem;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  text-decoration: none;
  transition: transform 0.2s, box-shadow 0.2s;
}

.quick-access-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.quick-access-card h3 {
  font-size: 1.2rem;
  color: #334e68;
  margin-bottom: 0.5rem;
}

.quick-access-card p {
  color: #627d98;
}

.btn {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
}

.btn-primary {
  background-color: #486581;
  color: white;
}

.btn-secondary {
  background-color: #e2e8f0;
  color: #334e68;
}
</style>