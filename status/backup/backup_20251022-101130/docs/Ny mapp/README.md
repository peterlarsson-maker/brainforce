# BrainForce Core – v2.0.0 (Backup Snapshot)

## Översikt
BrainForce Core är den centrala intelligenta motorn i BrainForce-ekosystemet.  
Den hanterar AI-runtime, policyer, återställning, minnesstyrning och självdiagnostik.

## Struktur
- **ai_engine/** – huvudmotor, minneshantering, policy-runtime.
- **manifests/** – systemvalidering enligt comcent-standard.
- **license_validator.py** – kontrollerar licensnivåer.
- **recovery.py** – självläkning och state rollback.

## Status (2025-10-15)
✅ Funktionell, självlärande och licensierbar  
✅ Manifestlager och validering klara  
⚙️ Kvar att färdigställa:
1. Full Hub-integration (OAuth + API tokens)
2. Dokumentation för `brainforce_config.json`
3. Test med Multi-AI-panel (synk mot UI)
4. Prestandaloggar + profileringsverktyg

## Version
- **BrainForce Core:** v2.0.0  
- **Manifest:** v1.0.0  
- **Status:** Beta-stabil (8.3/10)

## Backup
För att skapa backup:
```bash
zip -r brainforce_core_backup_2025-10-15.zip brainforce_core/
```

Förvara på extern SSD och i krypterat molnarkiv.
