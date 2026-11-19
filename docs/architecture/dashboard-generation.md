# Dashboard Generation Architecture

## 1. Purpose and Scope

Patrimonia provides a mechanism for generating financial dashboards in HTML from data produced by its application services.

The proposed architecture combines **Python, Plotly and Jinja2** to generate static HTML pages containing interactive visualizations.

The generated dashboards are intended to:
- Be generic and reusable across users and wallets.
- Be configurable through YAML resources.
- Separate financial data from visualization definitions and page layouts.
- Be easy to maintain and extend.
- Be viewable directly in a web browser without running the Patrimonia application.
- Support standalone HTML files that can be viewed offline.

This document describes the target architecture and design principles. It does not imply that all components and workflows are already implemented.

## 2. Selected Technologies

### 2.1. Python — Data Preparation and Orchestration

Python is responsible for orchestrating dashboard generation and preparing the data required by visualizations.

It handles:
- Retrieving calculated application data through the appropriate repositories or services.
- Preparing data for graphical representation.
- Loading and validating dashboard configuration.
- Building Plotly figures.
- Rendering HTML templates.
- Writing the final HTML files.

Dashboard generation should consume validated application data rather than independently reimplementing financial calculations.

### 2.2. Plotly — Interactive Charts

[Plotly](https://plotly.com/python/) is used to build interactive charts from data prepared by Python.

It supports several visualization types, including:
- Time-series charts.
- Allocation charts, such as pie charts and treemaps.
- Comparative bar charts.
- Financial charts, including candlestick charts.
- Heatmaps and other specialized visualizations.

Plotly provides built-in interactions such as:
- Zooming and panning.
- Hover information.
- Showing and hiding data series.
- Selecting and exploring data.

Plotly figures can be converted into HTML fragments containing the JavaScript required to render and interact with the charts.

### 2.3. Jinja2 — HTML Templates

[Jinja2](https://jinja.palletsprojects.com/) is used as the HTML template engine.

It separates page structure from the data and visualizations displayed in the dashboard.

Templates define reusable page elements, including:
- Headers and footers.
- Sections and containers.
- Titles and subtitles.
- Tables and indicators.
- Chart placement and layout.

Template inheritance and reusable components help maintain a consistent structure across dashboards.

### 2.4. CSS — Visual Presentation

CSS defines the visual appearance of dashboards.

It handles:
- Page layout.
- Typography.
- Colors.
- Spacing.
- Responsive behavior across screen sizes.

Styles should be shared wherever possible to ensure a consistent visual identity across dashboards.

### 2.5. JavaScript — Additional Interactions

Plotly already provides the JavaScript functionality required for standard chart interactions.

Custom JavaScript is therefore optional and should only be introduced when a specific dashboard requirement cannot be handled by Plotly or the HTML template.

Examples may include:
- Additional page-level interactions.
- Dynamic display of dashboard sections.
- Custom controls shared by several charts.

Custom scripts should remain limited to presentation-related behavior. Financial calculations and business logic belong in Python.

## 3. Generation Workflow

Dashboard generation follows a sequence of distinct steps:

1. **Data retrieval**: obtain the relevant calculated data through the application's data access components.
2. **Data preparation**: transform the retrieved data into structures suitable for visualization.
3. **Configuration loading**: load the dashboard and chart definitions from YAML resources.
4. **Configuration validation**: validate dashboard definitions and their parameters against the corresponding JSON Schemas.
5. **Chart generation**: construct Plotly figures using the prepared data and chart definitions.
6. **HTML rendering**: inject the chart fragments and prepared data into Jinja2 templates.
7. **Resource integration**: include the required CSS and JavaScript resources.
8. **Export**: write the final HTML document to the configured output directory.

The result is an HTML file that can be opened directly in a web browser.

The generation process does not require a web application server. Once generated, the dashboard is independent of the Python application, subject to the availability of its embedded or externally loaded browser resources.

## 4. Resource Organization

Dashboard resources are maintained separately from user data and generated output.

An illustrative organization is:

```text
resources/
├── schemas/
│   └── users/
│       └── dashboards/
│
├── rules/
│   └── users/
│       └── dashboards/
│           ├── portfolio_evolution.yaml
│           └── portfolio_allocation.yaml
│
├── templates/
│   └── users/
│       └── dashboards/
│           ├── dashboard.html
│           └── components/
│               ├── header.html
│               └── footer.html
│
├── styles/
│   └── dashboards/
│       └── dashboard.css
│
└── scripts/
    └── dashboards/
```

The exact directory structure may evolve as the number and types of dashboards increase.

### 4.1. Resource Responsibilities

| Resource | Responsibility |
|---|---|
| `schemas/` | Define and validate the structure of dashboard and chart configuration files. |
| `rules/` | Describe chart definitions and visualization parameters. |
| `templates/` | Define the HTML page structure and reusable components. |
| `styles/` | Define the visual presentation of dashboards. |
| `scripts/` | Provide optional custom JavaScript functionality. |

The resources under `resources/` are application resources. They must not be confused with user-specific calculated data or generated HTML files.

## 5. Separation of Responsibilities

A fundamental design principle is the separation between financial data, chart definitions and dashboard page layouts.

### 5.1. Financial Data

Financial data is produced by the application's existing calculation workflows.

Dashboard generation consumes these results without modifying their source data or duplicating the underlying financial calculations.

Data preparation may reshape or aggregate existing results for visualization purposes, but it must not introduce a separate implementation of business calculations.

### 5.2. Chart Definitions

Chart definitions are stored in YAML files.

They describe how a visualization should be constructed, including:
- Chart type.
- Data source or data reference.
- Series to display.
- X and Y axes.
- Units and value formats.
- Colors.
- Legends.
- Titles and labels.
- Supported interaction parameters.

Chart definitions describe visualization behavior rather than financial business rules.

The YAML format should remain declarative and simple. Complex transformations and calculations should be implemented in Python rather than encoded in configuration files.

### 5.3. Dashboard Templates

Jinja2 templates define how visualizations and other dashboard elements are arranged on a page.

They describe:
- Chart placement.
- Section organization.
- Titles and subtitles.
- Tables and indicators.
- Headers and footers.
- Shared page components.

Templates should not contain financial calculations or chart-generation logic.

### 5.4. Reusability

This separation makes it possible to:
- Reuse a chart definition in several dashboards.
- Reuse a page template with different datasets.
- Generate dashboards for different users and wallets.
- Change the visual presentation without modifying financial calculations.

## 6. Application Configuration

Dashboard generation is configured through the application's configuration system.

An illustrative configuration is:

```yaml
dashboards:
  format: html
  filename: <USER_ID>_dashboard.html
  folder: external-data/users/<USER_ID>/calculated/dashboards

  schemas: resources/schemas/users/dashboards
  rules: resources/rules/users/dashboards
  templates: resources/templates/users/dashboards
  styles: resources/styles/dashboards
  scripts: resources/scripts/dashboards
```

The configuration defines:
- The output format.
- The generated filename.
- The output directory.
- The locations of the resources required for generation.

The application configuration is loaded at startup and passed to the components that need it. Dashboard components should not independently reload the application configuration.

The example above illustrates the intended organization. The final configuration structure should be aligned with the existing configuration conventions and path-resolution mechanisms.

## 7. Python Generation Components

Dashboard generation should be orchestrated by a dedicated application service.

A possible design is:

### 7.1. DashboardService

`DashboardService` orchestrates the dashboard generation use case.

Its responsibilities include:
- Identifying the requested dashboard.
- Retrieving the required calculated data.
- Loading the relevant dashboard configuration.
- Requesting the generation of charts and HTML.
- Coordinating the export of the final result.

It should delegate file access and rendering operations to specialized components.

### 7.2. DashboardGenerator

`DashboardGenerator` is a proposed technical component responsible for rendering the dashboard.

Its responsibilities may include:
- Building Plotly figures from prepared data and chart definitions.
- Loading Jinja2 templates.
- Injecting chart fragments and dashboard data into templates.
- Integrating CSS and optional JavaScript resources.
- Producing the final HTML document.

The generator should not retrieve financial data directly from user files or implement financial business rules.

### 7.3. Supporting Components

As the implementation evolves, responsibilities may be delegated to specialized components, for example:
- A configuration loader and validator.
- A chart builder responsible for Plotly figures.
- An HTML renderer responsible for Jinja2 templates.
- An exporter responsible for writing the generated files.

These components should only be introduced when they provide a clear separation of responsibilities. A single generic generator is sufficient for an initial implementation.

## 8. HTML Portability and Offline Usage

Generated dashboards are intended to be opened directly in a browser, without running a Python server.

Two approaches are possible.

### 8.1. Standalone HTML

The required JavaScript libraries and styles are embedded in the generated HTML document.

For Plotly, the HTML export must include the Plotly.js library, for example through Plotly's `include_plotlyjs=True` option.

CSS and any required custom JavaScript must also be embedded or otherwise made available locally.

Advantages:
- No external server is required.
- No CDN access is required.
- The dashboard can be moved as a single file.
- Offline viewing is supported, provided all required resources are embedded and the browser supports the generated content.

This is the preferred approach for Patrimonia.

### 8.2. HTML with CDN Resources

Alternatively, JavaScript libraries can be loaded from a Content Delivery Network (CDN).

Advantages:
- Smaller HTML files.
- Shared external library resources.
- Potentially reduced duplication across dashboards.

Limitations:
- An Internet connection is generally required.
- The dashboard depends on the availability of external resources.
- Long-term portability is reduced.

This approach may be considered if file size becomes a significant concern.

## 9. Architectural Principles

The dashboard generation architecture follows these principles:

1. **Separation of concerns**: financial calculations, data preparation, chart definitions and page rendering remain independent.
2. **Reusability**: chart definitions, templates and styles can be shared across dashboards.
3. **Configuration-driven generation**: YAML resources describe visualization parameters without embedding complex business logic.
4. **Validation**: dashboard configuration is validated before it is used.
5. **Consistency**: generated dashboards use shared templates and styles.
6. **Portability**: standalone HTML is the preferred output.
7. **Layer separation**: application services orchestrate the use case, while specialized components handle data access and rendering.

## 10. Technology Summary

| Technology | Responsibility |
|---|---|
| Python | Data preparation and generation orchestration |
| JSON Schema | Validation of dashboard configuration |
| YAML | Declarative chart and dashboard definitions |
| Plotly | Interactive chart generation |
| Jinja2 | HTML page rendering |
| CSS | Visual presentation |
| JavaScript | Optional additional browser-side interactions |

**Guiding principle:** financial data, visualization definitions, chart generation and page layout must remain independent.

This architecture provides a reusable foundation for generating financial dashboards while remaining consistent with Patrimonia's overall application architecture.