BASH_COMPLETION = """# bash completion for zhirta
_zhirta_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="diagnose system logs history explain config analyze version help"

    case "${prev}" in
        diagnose)
            COMPREPLY=( $(compgen -W "audio network gpu storage systemd packages display gaming full" -- ${cur}) )
            return 0
            ;;
        config)
            COMPREPLY=( $(compgen -W "set get" -- ${cur}) )
            return 0
            ;;
        set)
            COMPREPLY=( $(compgen -W "model api-key api-url provider temperature max-tokens" -- ${cur}) )
            return 0
            ;;
        *)
            ;;
    esac

    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
}
complete -F _zhirta_completion zhirta
"""

ZSH_COMPLETION = """#compdef zhirta

_zhirta() {
    local -a commands
    commands=(
        'diagnose:Run automated system health audits'
        'system:Display hardware, OS, and resource telemetry'
        'logs:View or analyze system journal error logs'
        'history:View previous command execution records'
        'explain:Break down a Linux command, its flags, and risks'
        'config:Manage AI provider and application settings'
        'analyze:Analyze piped log or error text with AI'
        'version:Show version information'
        'help:Show help summary'
    )

    _arguments \
        '1: :->command' \
        '*: :->args'

    case $state in
        command)
            _describe 'command' commands
            ;;
        args)
            case $words[1] in
                diagnose)
                    _values 'categories' audio network gpu storage systemd packages display gaming full
                    ;;
                config)
                    _values 'actions' set get
                    ;;
            esac
            ;;
    esac
}
"""

FISH_COMPLETION = """# fish completion for zhirta
complete -c zhirta -f
complete -c zhirta -n "__fish_use_subcommand" -a diagnose -d "Run system diagnostics"
complete -c zhirta -n "__fish_use_subcommand" -a system -d "Display hardware and OS info"
complete -c zhirta -n "__fish_use_subcommand" -a logs -d "Inspect system error logs"
complete -c zhirta -n "__fish_use_subcommand" -a history -d "View command execution history"
complete -c zhirta -n "__fish_use_subcommand" -a explain -d "Explain shell command"
complete -c zhirta -n "__fish_use_subcommand" -a config -d "Configure AI settings"
complete -c zhirta -n "__fish_use_subcommand" -a analyze -d "Analyze piped log text"
complete -c zhirta -n "__fish_use_subcommand" -a version -d "Show version"
"""

def get_completion_script(shell: str) -> str:
    s = shell.lower().strip()
    if s == "zsh":
        return ZSH_COMPLETION
    elif s == "fish":
        return FISH_COMPLETION
    return BASH_COMPLETION
