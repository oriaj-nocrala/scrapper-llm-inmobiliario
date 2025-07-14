"""
Professional AssetPlan Scraper - Main entry point with full orchestration.
"""
import argparse
import sys

from .domain.data_validator import DataQualityReporter
from .services.logging_config import setup_logging, setup_selenium_logging
from .services.scraper_manager import (ScraperManager, ScrapingConfig,
                                       scrape_properties_comprehensive,
                                       scrape_properties_quick)


def main():
    """Main entry point for the professional scraper."""
    parser = argparse.ArgumentParser(
        description="Professional AssetPlan.cl Property Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default mode (extreme speed, maximum performance)
  python -m src.scraper.professional_scraper --max-properties 50
  
  # Quick scrape (extreme speed, minimal properties)
  python -m src.scraper.professional_scraper --quick --max-properties 10
  
  # Human-like behavior (slower but more stable)
  python -m src.scraper.professional_scraper --human-like --max-properties 25
  
  # Comprehensive mode (human-like + validation + monitoring)
  python -m src.scraper.professional_scraper --comprehensive --max-properties 50
  
  # Conservative mode (slower, more stable, with validation)
  python -m src.scraper.professional_scraper --conservative --max-properties 25
  
  # Debug mode with visual browser
  python -m src.scraper.professional_scraper --debug --max-properties 5
        """)
    
    # Basic configuration
    parser.add_argument(
        "--max-properties", "-n",
        type=int,
        default=50,
        help="Maximum number of properties to scrape (default: 50)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file path (default: data/properties.json)"
    )
    
    # Behavior configuration
    parser.add_argument(
        "--behavior",
        choices=["extreme", "fast", "normal", "slow", "very_slow"],
        default="extreme",
        help="Scraping behavior mode (default: extreme)"
    )
    
    parser.add_argument(
        "--retry",
        choices=["fast", "standard", "aggressive", "patient"],
        default="fast",
        help="Retry strategy (default: fast)"
    )
    
    parser.add_argument(
        "--circuit-breaker",
        choices=["sensitive", "standard", "tolerant"],
        default="tolerant",
        help="Circuit breaker sensitivity (default: tolerant)"
    )
    
    # Feature flags
    parser.add_argument(
        "--enable-detail-extraction",
        action="store_true",
        help="Enable detailed property page extraction (slower but more complete)"
    )
    
    parser.add_argument(
        "--enable-validation",
        action="store_true",
        help="Enable data validation and cleaning (disabled by default for speed)"
    )
    
    parser.add_argument(
        "--enable-monitoring",
        action="store_true",
        help="Enable performance monitoring (disabled by default for speed)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with visual browser for debugging"
    )
    
    parser.add_argument(
        "--human-like",
        action="store_true",
        help="Enable human-like behavior simulation (delays, random movements)"
    )
    
    parser.add_argument(
        "--conservative",
        action="store_true",
        help="Conservative mode: slower, more stable, with validation and monitoring"
    )
    
    # Preset modes
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: fast scraping with minimal features"
    )
    
    parser.add_argument(
        "--comprehensive",
        action="store_true",
        help="Comprehensive mode: human-like behavior, validation, detailed extraction"
    )
    
    # Logging configuration
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Log file path (default: console only)"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode: minimal console output"
    )
    
    # URL configuration
    parser.add_argument(
        "--url",
        type=str,
        default="https://www.assetplan.cl/arriendo/departamento",
        help="Base URL to scrape (default: AssetPlan apartments for rent page)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(
        log_level=args.log_level,
        log_file=args.log_file,
        service_name="professional_scraper",
        enable_console=not args.quiet,
        enable_structured=True
    )
    setup_selenium_logging("ERROR" if args.quiet else "WARNING")
    
    logger.info("Professional AssetPlan Scraper starting", extra={
        "version": "2.0.0",
        "max_properties": args.max_properties,
        "behavior_mode": args.behavior,
        "url": args.url
    })
    
    try:
        # Handle preset modes
        if args.quick:
            logger.info("Using quick preset mode (extreme speed)")
            collection = scrape_properties_quick(max_properties=args.max_properties)
            
        elif args.comprehensive:
            logger.info("Using comprehensive preset mode (human-like behavior)")
            collection = scrape_properties_comprehensive(max_properties=args.max_properties)
            
        elif args.conservative:
            logger.info("Using conservative preset mode")
            config = ScrapingConfig(
                max_properties=args.max_properties,
                behavior_mode="normal",
                retry_strategy="standard",
                circuit_breaker_mode="standard",
                enable_validation=True,
                enable_performance_monitoring=True,
                human_like_behavior=args.human_like,
                debug_mode=args.debug
            )
            with ScraperManager(config) as manager:
                collection = manager.scrape_properties(base_url=args.url)
            
        else:
            # Custom configuration (defaults to extreme mode)
            behavior_mode = args.behavior if hasattr(args, 'behavior') else "extreme"
            retry_strategy = args.retry if hasattr(args, 'retry') else "fast"
            circuit_breaker = args.circuit_breaker if hasattr(args, 'circuit_breaker') else "tolerant"
            human_like = args.human_like
            
            # Custom configuration
            config = ScrapingConfig(
                max_properties=args.max_properties,
                enable_detail_page_extraction=args.enable_detail_extraction,
                behavior_mode=behavior_mode,
                retry_strategy=retry_strategy,
                circuit_breaker_mode=circuit_breaker,
                enable_validation=args.enable_validation,  # Now defaults to False
                enable_performance_monitoring=args.enable_monitoring,  # Now defaults to False
                output_file=args.output,
                debug_mode=args.debug,
                human_like_behavior=human_like
            )
            
            # Progress callback for console output
            def progress_callback(data):
                if not args.quiet:
                    print(f"\r{data['message']} ({data['percentage']:.1f}%)", end="", flush=True)
            
            with ScraperManager(config, logger) as manager:
                collection = manager.scrape_properties(
                    base_url=args.url,
                    progress_callback=progress_callback
                )
            
            if not args.quiet:
                print()  # New line after progress
        
        # Generate and display results
        _display_results(collection, logger, args.quiet)
        
        # Generate data quality report if validation was enabled
        if args.enable_validation and collection.properties:
            from .domain.data_validator import PropertyCollectionValidator
            validator = PropertyCollectionValidator()
            _, validation_summary = validator.validate_collection(collection.properties)
            
            if not args.quiet:
                quality_report = DataQualityReporter.generate_report(
                    collection.properties, 
                    validation_summary
                )
                print("\n" + quality_report)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        print("\nScraping interrupted by user")
        return 1
        
    except Exception as e:
        logger.error_with_context("Scraping failed with unexpected error", e)
        print(f"\nError: {e}")
        return 1


def _display_results(collection, logger, quiet_mode):
    """Display scraping results.
    
    Args:
        collection: PropertyCollection results
        logger: Logger instance
        quiet_mode: Whether to suppress detailed output
    """
    logger.info("Scraping completed", extra={
        "total_properties": collection.total_count,
        "source_url": collection.source_url
    })
    
    if not quiet_mode:
        print(f"\n{'='*60}")
        print("SCRAPING RESULTS")
        print(f"{'='*60}")
        print(f"Total Properties Scraped: {collection.total_count}")
        print(f"Source URL: {collection.source_url}")
        print(f"Scraped At: {collection.scraped_at}")
        
        if collection.properties:
            print(f"\nSample Properties:")
            for i, prop in enumerate(collection.properties[:3]):
                print(f"\n{i+1}. {prop.title}")
                print(f"   Price: {prop.price or 'N/A'}")
                print(f"   Location: {prop.location or 'N/A'}")
                print(f"   URL: {prop.url}")
        
        print(f"\n{'='*60}")


if __name__ == "__main__":
    sys.exit(main())