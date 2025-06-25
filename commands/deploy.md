@include shared/constants.yml#Process_Symbols

@include shared/command-templates.yml#Universal_Flags

Deploy application to env specified in $ARGUMENTS.

Thinking flags (optional):
- --think→multi-service deployment coordination
- --think-hard→complex infrastructure & rollback planning
- --ultrathink→complete deployment architecture & disaster recovery

Examples:
- `/user:deploy --env staging --think` - Staging w/ coordination analysis
- `/user:deploy --env prod --think-hard` - Prod w/ comprehensive planning
- `/user:deploy --rollback --ultrathink` - Critical rollback w/ full impact analysis

Pre-deploy cleanup:
- Clean previous artifacts | Remove dev-only files (.env.local, debug cfgs)
- Validate prod cfg (no debug flags, correct URLs) | Clean old versions→free space

--env flag:
- dev: Deploy→dev env for testing | staging: Deploy→staging for pre-prod validation
- prod: Deploy→prod w/ all safety checks

--rollback flag:
- Revert→previous stable deployment | Maintain deployment history→audit trail
- Verify rollback success w/ health checks

Deployment workflow:
1. Validate→Check prerequisites & cfg 2. Build→Create artifacts 3. Test→Run smoke tests
4. Deploy→Execute strategy 5. Verify→Confirm health & functionality

Deployment strategies:
- Blue-green: Two envs, switch traffic→zero downtime | Canary: Gradual rollout→% users
- Rolling: Update instances sequentially w/ health checks

Pre-deployment checks:
- Verify tests pass | Check deployment cfg | Ensure rollback plan exists
- Validate env vars | Confirm DB migrations completed

Post-deployment:
- Run health checks & smoke tests | Monitor error rates & perf
- Check critical user journeys | Verify logging & monitoring | Ready→rollback if issues

## Safety & Best Practices

Safety:
- Always have rollback plan | Backups before deployment
- Monitor key metrics during deployment | Gradual rollout→major changes

@include shared/command-templates.yml#Research_Requirements

@include shared/command-templates.yml#Report_Output

@include shared/constants.yml#Success_Messages