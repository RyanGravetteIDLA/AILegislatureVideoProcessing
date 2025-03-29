<template>
  <div>
    <h1 class="page-title">Sitemap</h1>
    <p class="page-description">Navigate through all sections of the Idaho Legislature Media site</p>
    
    <div class="section">
      <h2 class="section-title">Main Pages</h2>
      
      <div class="link-section">
        <h3>
          <router-link to="/" class="link">Dashboard</router-link>
        </h3>
        <p>Overview of the Idaho Legislature Media library with quick access to all sections.</p>
        <ul>
          <li>Statistics overview</li>
          <li>Recent media items</li>
          <li>Quick access to all sections</li>
        </ul>
      </div>
      
      <div class="link-section">
        <h3>
          <router-link to="/videos" class="link">Video Library</router-link>
        </h3>
        <p>Browse and search through Idaho legislative session videos.</p>
        <ul>
          <li>Filter by year, category, and keyword</li>
          <li>View detailed information about each video</li>
          <li>Watch videos directly or download them</li>
        </ul>
      </div>
      
      <div class="link-section">
        <h3>
          <router-link to="/audio" class="link">Audio Library</router-link>
        </h3>
        <p>Browse and search through Idaho legislative session audio recordings.</p>
        <ul>
          <li>Filter by year, category, and keyword</li>
          <li>Listen to audio recordings directly</li>
          <li>Download audio files</li>
        </ul>
      </div>
      
      <div class="link-section">
        <h3>
          <router-link to="/transcripts" class="link">Transcript Library</router-link>
        </h3>
        <p>Browse and search through Idaho legislative session transcripts.</p>
        <ul>
          <li>Filter by year, category, and keyword</li>
          <li>View transcript details</li>
          <li>Download transcript files</li>
        </ul>
      </div>
    </div>
    
    <div class="section">
      <h2 class="section-title">Administrative</h2>
      
      <div class="link-section">
        <h3>
          <router-link to="/admin" class="link">Admin Dashboard</router-link>
        </h3>
        <p>Administrative dashboard for managing content (requires authentication).</p>
        <ul>
          <li>Manage media files</li>
          <li>Upload new content</li>
          <li>Edit metadata</li>
          <li>Monitor system status</li>
        </ul>
      </div>
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

.section {
  background-color: white;
  padding: 1.5rem;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 1.5rem;
  color: #334e68;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 0.5rem;
}

.link-section {
  margin-bottom: 2rem;
}

.link-section:last-child {
  margin-bottom: 0;
}

.link-section h3 {
  font-size: 1.2rem;
  margin-bottom: 0.5rem;
}

.link {
  color: #486581;
  text-decoration: none;
}

.link:hover {
  color: #334e68;
  text-decoration: underline;
}

.link-section p {
  color: #627d98;
  margin-bottom: 0.5rem;
}

.link-section ul {
  list-style-type: disc;
  margin-left: 1.5rem;
  color: #627d98;
}

.link-section li {
  margin-bottom: 0.25rem;
}
</style>