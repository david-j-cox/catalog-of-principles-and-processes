# Behavioral Process Catalog

A retro-themed web application for cataloging behavioral processes from the Journal of Experimental Analysis of Behavior (JEAB). Built with a 1990s science aesthetic celebrating biology, nature, and biodiversity.

## Live Demo

Visit the live site: [URL Coming]

## Features

- **Interactive Data Table**: Browse articles with columns for title, year, volume, issue, behavioral process, and IV→DV equations
- **Search & Filter**: Real-time search across all fields with filtering by year and behavioral process
- **Add New Entries**: Modal form to add new research articles to the catalog
- **Statistics Dashboard**: Overview of catalog metrics and database statistics
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Data Persistence**: Entries are saved in browser localStorage and generate pull request to site owner to approve or deny
- **Retro Science Theme**: 1990s-inspired design with neon colors and geometric patterns

## Design Theme

The application features a distinctive 1990s retro science aesthetic:
- **Neon Color Palette**: Bright greens (#00ff88), cyans (#00ccff), and purples (#9933ff)
- **Typography**: Orbitron and Space Mono fonts for that futuristic feel
- **Animations**: Smooth transitions, glowing effects, and floating elements
- **Biology-Inspired**: Color schemes and visual elements celebrating nature and biodiversity


## Usage

### Viewing the Catalog
- **Browse**: Navigate through the data table to view all entries
- **Search**: Use the search bar to find specific articles, processes, or equations
- **Filter**: Use dropdown filters to narrow results by year or behavioral process
- **Sort**: Click column headers to sort data (future enhancement)

### Adding New Entries
1. Click the "+ Add New Entry" button
2. Fill in the modal form with article details:
   - Article Title
   - Publication Year
   - Volume Number
   - Issue Number
   - Behavioral Process Studied
   - IV → DV Equation (optional)
3. Click "Add Entry" to save

### Keyboard Shortcuts
- `Ctrl+K` (or `Cmd+K`): Focus search input
- `Ctrl+Enter` (or `Cmd+Enter`): Open add entry modal
- `Escape`: Close modal

## Customization

### Adding More Sample Data
Edit the `behavioralData` array in `script.js`:

```javascript
{
    title: "Your Article Title",
    year: 2024,
    volume: 120,
    issue: 1,
    abstract: "Enter abstract"
    process: "Behavioral Process Name",
    equation: "Mathematical Equation"
}
```

### Styling Modifications
The CSS uses CSS custom properties (variables) for easy theme customization:

```css
:root {
    --primary-neon: #00ff88;    /* Main accent color */
    --secondary-neon: #00ccff;  /* Secondary accent */
    --accent-purple: #9933ff;   /* Third accent color */
    --bg-dark: #0a0a0a;        /* Dark background */
    --bg-card: #1a1a2e;        /* Card background */
    /* ... more variables */
}
```

## Responsive Features

- Mobile-optimized table layout
- Collapsible navigation for small screens
- Touch-friendly interface elements
- Responsive grid layouts for cards and statistics

## Data Management

- **Local Storage**: All data persists in browser localStorage
- **Export Capability**: Future enhancement for data export
- **Import Functionality**: Potential for CSV/JSON import features

## Technical Stack

- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Custom CSS with CSS Grid and Flexbox
- **Fonts**: Google Fonts (Orbitron, Space Mono)
- **Storage**: Browser localStorage
- **Deployment**: GitHub Pages

## File Structure

```
catalog-of-principles-and-processes/
├── index.html          # Main HTML structure
├── styles.css          # Retro theme CSS styling
├── script.js           # Application functionality
└── README.md           # Documentation
```

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).

## About JEAB

The Journal of Experimental Analysis of Behavior (JEAB) is a leading publication in behavior analysis, publishing research on fundamental behavioral processes across species. This catalog aims to make the rich history of behavioral research more accessible and searchable.

---

**Built with 💚 for the behavior analysis community**
