import scraper
import ai_engine
import config
import json

def test_scraper():
    print("Testing Scraper Engine...")
    url = "https://example.com"
    result = scraper.scrape_url(url)
    
    assert result['success'] is True, f"Scraper failed: {result.get('error')}"
    assert result['title'] == "Example Domain", f"Unexpected title: {result['title']}"
    assert "Example Domain" in result['content'], "Content did not contain key text"
    assert result['word_count'] > 0, "Word count should be positive"
    
    print("[OK] Scraper test passed!")
    print(f"Title: {result['title']}")
    print(f"Word Count: {result['word_count']}")
    print(f"Content Summary: {result['content'][:150]}...")
    print("-" * 50)
    return result

def test_config():
    print("Testing Configuration Module...")
    cfg = config.load_config()
    assert isinstance(cfg, dict), "Config should be a dictionary"
    assert 'gemini_api_key' in cfg, "Config should contain gemini_api_key"
    assert 'default_provider' in cfg, "Config should contain default_provider"
    
    # Test saving
    test_key = "test_key_12345"
    old_key = cfg.get('gemini_api_key', '')
    
    cfg['gemini_api_key'] = test_key
    config.save_config(cfg)
    
    # Reload and assert
    reloaded = config.load_config()
    assert reloaded['gemini_api_key'] == test_key, "Config did not save gemini_api_key correctly"
    
    # Restore
    reloaded['gemini_api_key'] = old_key
    config.save_config(reloaded)
    
    print("[OK] Configuration test passed!")
    print("-" * 50)

def test_ai_presets():
    print("Testing AI Presets...")
    assert len(ai_engine.PRESETS) > 0, "No AI presets found"
    for preset in ai_engine.PRESETS:
        assert 'name' in preset, "Preset missing name"
        assert 'system_prompt' in preset, "Preset missing system_prompt"
    print("[OK] AI Presets test passed!")
    print("-" * 50)

if __name__ == "__main__":
    print("Starting Automated Verification Tests...\n")
    try:
        scraped = test_scraper()
        test_config()
        test_ai_presets()
        print("[SUCCESS] All tests passed successfully!")
    except AssertionError as e:
        print(f"[ERROR] Test assertion failed: {e}")
    except Exception as e:
        print(f"[ERROR] Test encountered an error: {e}")
